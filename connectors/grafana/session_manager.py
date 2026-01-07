import asyncio
from collections import OrderedDict
import logging
from typing import Any, Dict, Optional, List
import httpx
from schema import GrafanaConfig, AuthType


logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages HTTP sessions for multiple Grafana instances.

    Similar to database connection pooling, this manager maintains
    httpx.AsyncClient instances for each server, implements LRU eviction,
    and handles cleanup of idle sessions.
    """

    def __init__(
        self, global_max_sessions=100, per_target_max=10, idle_ttl=300
    ):
        """
        Initialize the SessionManager.

        Args:
            global_max_sessions: Maximum total sessions across all servers
            per_target_max: Maximum sessions per individual server
            idle_ttl: Time-to-live for idle sessions in seconds
        """
        self.global_max = global_max_sessions
        self.per_target_max = per_target_max
        self.idle_ttl = idle_ttl
        # key -> (session, last_used, server_config)
        self.sessions = OrderedDict()
        self.total_sessions = 0
        self.lock = asyncio.Lock()

    def _get_auth_headers(self, config: GrafanaConfig) -> Dict[str, str]:
        """
        Generate authentication headers based on config.

        Args:
            config: GrafanaConfig with auth settings

        Returns:
            Dictionary with Authorization header
        """
        if config.auth_type == AuthType.SERVICE_ACCOUNT_TOKEN:
            if not config.service_account_token:
                raise ValueError(
                    "service_account_token is required when using "
                    "SERVICE_ACCOUNT_TOKEN auth"
                )
            return {
                "Authorization": f"Bearer {config.service_account_token}"
            }
        else:  # API_KEY
            if not config.api_key:
                raise ValueError(
                    "api_key is required when using API_KEY auth"
                )
            return {"Authorization": f"Bearer {config.api_key}"}

    async def _create_session(
        self, server_config: GrafanaConfig
    ) -> httpx.AsyncClient:
        """
        Create a new HTTP session for a Grafana instance.

        Args:
            server_config: GrafanaConfig with connection settings

        Returns:
            Configured httpx.AsyncClient instance
        """
        headers = self._get_auth_headers(server_config)

        # Add any additional headers from config
        if server_config.additional_params:
            headers.update(server_config.additional_params)

        # Ensure base URL doesn't have trailing slash
        base_url = server_config.grafana_url.rstrip('/')

        session = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=server_config.timeout,
            verify=server_config.verify_ssl,
            follow_redirects=True
        )

        return session

    async def get_session(
        self, server_id: str, server_config: GrafanaConfig
    ) -> httpx.AsyncClient:
        """
        Get or create a session for a server.

        Args:
            server_id: Unique identifier for the server
            server_config: GrafanaConfig with connection settings

        Returns:
            httpx.AsyncClient session for the server
        """
        key = server_id
        async with self.lock:
            if key in self.sessions:
                # Move to end (most recently used)
                session, _, _ = self.sessions.pop(key)
                self.sessions[key] = (
                    session,
                    asyncio.get_event_loop().time(),
                    server_config
                )
                return session

            # Create new session, but enforce global limits
            if self.total_sessions >= self.global_max:
                await self.evict_one()

            session = await self._create_session(server_config)
            self.sessions[key] = (
                session,
                asyncio.get_event_loop().time(),
                server_config
            )
            self.total_sessions += 1
            return session

    async def evict_one(self):
        """Evict the least recently used session."""
        if not self.sessions:
            return

        # Get the first (oldest) item
        key, (session, last_used, _) = next(iter(self.sessions.items()))
        await session.aclose()
        del self.sessions[key]
        self.total_sessions -= 1
        logger.info(f"Evicted session for server {key}")

    async def cleanup_loop(self):
        """Background task to cleanup idle sessions."""
        while True:
            await asyncio.sleep(self.idle_ttl / 2)
            now = asyncio.get_event_loop().time()
            async with self.lock:
                for key, (session, last_used, _) in list(self.sessions.items()):
                    if now - last_used > self.idle_ttl:
                        await session.aclose()
                        del self.sessions[key]
                        self.total_sessions -= 1
                        logger.info(f"Cleaned up idle session for server {key}")

    async def close_session(self, server_id: str) -> bool:
        """
        Close and remove a session for a specific server.

        Args:
            server_id: Unique identifier for the server

        Returns:
            True if session was found and closed, False otherwise
        """
        async with self.lock:
            if server_id in self.sessions:
                session, _, _ = self.sessions.pop(server_id)
                await session.aclose()
                self.total_sessions -= 1
                logger.info(f"Closed session for server {server_id}")
                return True
            return False

    async def _handle_response_error(
        self, response: httpx.Response, operation: str
    ):
        """
        Handle HTTP error responses with meaningful messages.

        Args:
            response: httpx.Response object
            operation: Description of the operation being performed

        Raises:
            Exception with descriptive error message
        """
        error_messages = {
            401: "Authentication failed. Please check your credentials.",
            403: "Permission denied. Insufficient privileges.",
            404: f"Resource not found for operation: {operation}",
            412: "Version conflict. Dashboard modified by another user.",
            500: "Grafana server error. Please check server logs.",
        }

        try:
            error_data = response.json()
            error_msg = error_data.get("message", str(error_data))
        except Exception:
            error_msg = response.text

        status_msg = error_messages.get(
            response.status_code, f"HTTP {response.status_code}"
        )
        raise Exception(f"{status_msg}: {error_msg}")

    async def list_dashboards(
        self,
        server_id: str,
        server_config: GrafanaConfig
    ) -> List[Dict[str, Any]]:
        """
        List all dashboards accessible to the authenticated user.
        
        Args:
            server_id: Unique identifier for the server
            server_config: GrafanaConfig with connection settings
            
        Returns:
            List of dashboard summaries
        """
        try:
            session = await self.get_session(server_id, server_config)
            params = {"type": "dash-db"}
            response = await session.get("/api/search", params=params)

            if response.status_code != 200:
                await self._handle_response_error(
                    response, "list dashboards"
                )

            return response.json()
        except Exception as e:
            logger.error(f"Failed to list dashboards: {str(e)}")
            raise

    async def get_dashboard(
        self,
        server_id: str,
        server_config: GrafanaConfig,
        uid: str
    ) -> Dict[str, Any]:
        """
        Get a specific dashboard by UID.

        Args:
            server_id: Unique identifier for the server
            server_config: GrafanaConfig with connection settings
            uid: Dashboard UID

        Returns:
            Dashboard object with metadata
        """
        try:
            session = await self.get_session(server_id, server_config)
            response = await session.get(f"/api/dashboards/uid/{uid}")

            if response.status_code != 200:
                await self._handle_response_error(
                    response, f"get dashboard {uid}"
                )

            return response.json()
        except Exception as e:
            logger.error(f"Failed to get dashboard {uid}: {str(e)}")
            raise

    async def create_dashboard(
        self,
        server_id: str,
        server_config: GrafanaConfig,
        dashboard: Dict[str, Any],
        folder_uid: Optional[str] = None,
        message: Optional[str] = None,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new dashboard.
        
        Args:
            server_id: Unique identifier for the server
            server_config: GrafanaConfig with connection settings
            dashboard: Dashboard JSON object
            folder_uid: UID of the folder to create dashboard in
            message: Commit message for dashboard creation
            overwrite: Whether to overwrite existing dashboard with same UID
            
        Returns:
            Response with dashboard UID, URL, and status
        """
        try:
            session = await self.get_session(server_id, server_config)
            
            payload = {
                "dashboard": dashboard,
                "overwrite": overwrite
            }
            
            if folder_uid:
                payload["folderUid"] = folder_uid
            
            if message:
                payload["message"] = message
            
            response = await session.post("/api/dashboards/db", json=payload)
            
            if response.status_code not in [200, 201]:
                await self._handle_response_error(response, "create dashboard")
            
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create dashboard: {str(e)}")
            raise

    async def update_dashboard(
        self,
        server_id: str,
        server_config: GrafanaConfig,
        dashboard: Dict[str, Any],
        overwrite: bool = True,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing dashboard.
        
        Args:
            server_id: Unique identifier for the server
            server_config: GrafanaConfig with connection settings
            dashboard: Dashboard JSON object with updated content
            overwrite: Whether to overwrite the existing dashboard
            message: Commit message for dashboard update
            
        Returns:
            Response with dashboard UID, URL, and status
        """
        try:
            session = await self.get_session(server_id, server_config)
            
            payload = {
                "dashboard": dashboard,
                "overwrite": overwrite
            }
            
            if message:
                payload["message"] = message
            
            response = await session.post("/api/dashboards/db", json=payload)
            
            if response.status_code != 200:
                await self._handle_response_error(response, "update dashboard")
            
            return response.json()
        except Exception as e:
            logger.error(f"Failed to update dashboard: {str(e)}")
            raise

    async def delete_dashboard(
        self,
        server_id: str,
        server_config: GrafanaConfig,
        uid: str
    ) -> Dict[str, Any]:
        """
        Delete a dashboard by UID.
        
        Args:
            server_id: Unique identifier for the server
            server_config: GrafanaConfig with connection settings
            uid: Dashboard UID to delete
            
        Returns:
            Response with deletion status
        """
        try:
            session = await self.get_session(server_id, server_config)
            response = await session.delete(f"/api/dashboards/uid/{uid}")
            
            if response.status_code != 200:
                await self._handle_response_error(response, f"delete dashboard {uid}")
            
            return response.json()
        except Exception as e:
            logger.error(f"Failed to delete dashboard {uid}: {str(e)}")
            raise

    async def search_dashboards(
        self,
        server_id: str,
        server_config: GrafanaConfig,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        folder_ids: Optional[List[int]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for dashboards with filters.
        
        Args:
            server_id: Unique identifier for the server
            server_config: GrafanaConfig with connection settings
            query: Search query string (searches title and tags)
            tags: List of tags to filter by
            folder_ids: List of folder IDs to search in
            limit: Maximum number of results to return
            
        Returns:
            List of matching dashboard summaries
        """
        try:
            session = await self.get_session(server_id, server_config)
            
            params = {
                "type": "dash-db",
                "limit": limit
            }
            
            if query:
                params["query"] = query
            
            if tags:
                params["tag"] = tags
            
            if folder_ids:
                params["folderIds"] = folder_ids
            
            response = await session.get("/api/search", params=params)
            
            if response.status_code != 200:
                await self._handle_response_error(response, "search dashboards")
            
            return response.json()
        except Exception as e:
            logger.error(f"Failed to search dashboards: {str(e)}")
            raise

    async def get_dashboard_permissions(
        self,
        server_id: str,
        server_config: GrafanaConfig,
        uid: str
    ) -> List[Dict[str, Any]]:
        """
        Get permissions for a dashboard.
        
        Args:
            server_id: Unique identifier for the server
            server_config: GrafanaConfig with connection settings
            uid: Dashboard UID
            
        Returns:
            List of permission entries
        """
        try:
            session = await self.get_session(server_id, server_config)
            response = await session.get(f"/api/dashboards/uid/{uid}/permissions")
            
            if response.status_code != 200:
                await self._handle_response_error(response, f"get permissions for dashboard {uid}")
            
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get dashboard permissions: {str(e)}")
            raise

    async def get_datasource_by_name(
        self,
        server_id: str,
        server_config: GrafanaConfig,
        name: str
    ) -> Dict[str, Any]:
        """
        Get a datasource by name and return its ID and details.

        Args:
            server_id: Unique identifier for the server
            server_config: GrafanaConfig with connection settings
            name: Name of the datasource to find

        Returns:
            Datasource object if found, or dict with exists=False if not
        """
        try:
            session = await self.get_session(server_id, server_config)
            response = await session.get("/api/datasources")

            if response.status_code != 200:
                await self._handle_response_error(
                    response, "list datasources"
                )

            datasources = response.json()

            # Find datasource by name (case-insensitive)
            for ds in datasources:
                if ds.get("name", "").lower() == name.lower():
                    return {
                        "id": ds.get("id"),
                        "uid": ds.get("uid"),
                        "name": ds.get("name"),
                        "type": ds.get("type"),
                        "url": ds.get("url"),
                        "isDefault": ds.get("isDefault", False),
                        "exists": True
                    }

            # Datasource not found
            return {
                "exists": False,
                "name": name,
                "message": f"Datasource '{name}' not found"
            }

        except Exception as e:
            logger.error(f"Failed to get datasource by name: {str(e)}")
            raise

    async def test_connection(
        self,
        server_id: str,
        server_config: GrafanaConfig
    ) -> Dict[str, Any]:
        """
        Test the connection to Grafana and return status information.

        Args:
            server_id: Unique identifier for the server
            server_config: GrafanaConfig with connection settings

        Returns:
            Dictionary with connection status and server information
        """
        try:
            session = await self.get_session(server_id, server_config)

            # Try health endpoint first
            response = await session.get("/api/health")

            if response.status_code == 200:
                health_data = response.json()

                # Get organization info for more details
                try:
                    org_response = await session.get("/api/org")
                    org_data = (
                        org_response.json()
                        if org_response.status_code == 200
                        else {}
                    )
                except Exception:
                    org_data = {}

                return {
                    "status": "connected",
                    "connected": True,
                    "grafana_url": server_config.grafana_url,
                    "auth_type": server_config.auth_type.value,
                    "health": health_data,
                    "organization": org_data.get("name", "Unknown"),
                    "version": health_data.get("version", "Unknown")
                }
            else:
                await self._handle_response_error(
                    response, "test connection"
                )

        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                "status": "error",
                "connected": False,
                "grafana_url": server_config.grafana_url,
                "auth_type": server_config.auth_type.value,
                "error": str(e)
            }

