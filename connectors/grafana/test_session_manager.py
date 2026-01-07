"""Unit tests for SessionManager"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from session_manager import SessionManager
from schema import GrafanaConfig, AuthType


@pytest.fixture
def grafana_config():
    """Create a test Grafana configuration"""
    return GrafanaConfig(
        grafana_url="https://grafana.example.com",
        auth_type=AuthType.SERVICE_ACCOUNT_TOKEN,
        service_account_token="test_token_123",
        verify_ssl=True,
        timeout=30
    )


@pytest.fixture
def session_manager():
    """Create a SessionManager instance for testing"""
    return SessionManager(
        global_max_sessions=10,
        per_target_max=5,
        idle_ttl=300
    )


class TestSessionManager:
    """Tests for SessionManager class"""
    
    @pytest.mark.asyncio
    async def test_get_auth_headers_service_account(self, session_manager, grafana_config):
        """Test authentication header generation for service account token"""
        headers = session_manager._get_auth_headers(grafana_config)
        assert headers == {"Authorization": "Bearer test_token_123"}
    
    @pytest.mark.asyncio
    async def test_get_auth_headers_api_key(self, session_manager):
        """Test authentication header generation for API key"""
        config = GrafanaConfig(
            grafana_url="https://grafana.example.com",
            auth_type=AuthType.API_KEY,
            api_key="api_key_456"
        )
        headers = session_manager._get_auth_headers(config)
        assert headers == {"Authorization": "Bearer api_key_456"}
    
    @pytest.mark.asyncio
    async def test_get_auth_headers_missing_token(self, session_manager):
        """Test that missing token raises ValueError"""
        config = GrafanaConfig(
            grafana_url="https://grafana.example.com",
            auth_type=AuthType.SERVICE_ACCOUNT_TOKEN,
            service_account_token=None
        )
        with pytest.raises(ValueError, match="service_account_token is required"):
            session_manager._get_auth_headers(config)
    
    @pytest.mark.asyncio
    async def test_create_session(self, session_manager, grafana_config):
        """Test session creation with proper configuration"""
        session = await session_manager._create_session(grafana_config)
        
        assert isinstance(session, httpx.AsyncClient)
        assert session.base_url == "https://grafana.example.com"
        assert "Authorization" in session.headers
        
        await session.aclose()
    
    @pytest.mark.asyncio
    async def test_get_session_creates_new(self, session_manager, grafana_config):
        """Test that get_session creates a new session if not exists"""
        server_id = "test_server_1"
        
        session = await session_manager.get_session(server_id, grafana_config)
        
        assert session is not None
        assert server_id in session_manager.sessions
        assert session_manager.total_sessions == 1
        
        await session_manager.close_session(server_id)
    
    @pytest.mark.asyncio
    async def test_get_session_reuses_existing(self, session_manager, grafana_config):
        """Test that get_session reuses existing session"""
        server_id = "test_server_1"
        
        session1 = await session_manager.get_session(server_id, grafana_config)
        session2 = await session_manager.get_session(server_id, grafana_config)
        
        assert session1 is session2
        assert session_manager.total_sessions == 1
        
        await session_manager.close_session(server_id)
    
    @pytest.mark.asyncio
    async def test_close_session(self, session_manager, grafana_config):
        """Test closing a session"""
        server_id = "test_server_1"
        
        await session_manager.get_session(server_id, grafana_config)
        assert server_id in session_manager.sessions
        
        result = await session_manager.close_session(server_id)
        
        assert result is True
        assert server_id not in session_manager.sessions
        assert session_manager.total_sessions == 0
    
    @pytest.mark.asyncio
    async def test_close_nonexistent_session(self, session_manager):
        """Test closing a session that doesn't exist"""
        result = await session_manager.close_session("nonexistent")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_evict_one(self, session_manager, grafana_config):
        """Test LRU eviction of sessions"""
        server_id = "test_server_1"
        
        await session_manager.get_session(server_id, grafana_config)
        assert session_manager.total_sessions == 1
        
        await session_manager.evict_one()
        
        assert session_manager.total_sessions == 0
        assert server_id not in session_manager.sessions


class TestSessionManagerAPI:
    """Tests for Grafana API operations"""
    
    @pytest.mark.asyncio
    async def test_list_dashboards_success(self, session_manager, grafana_config):
        """Test listing dashboards with successful response"""
        server_id = "test_server"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"uid": "dash1", "title": "Dashboard 1"},
            {"uid": "dash2", "title": "Dashboard 2"}
        ]
        
        with patch.object(session_manager, 'get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_get_session.return_value = mock_session
            
            result = await session_manager.list_dashboards(server_id, grafana_config)
            
            assert len(result) == 2
            assert result[0]["uid"] == "dash1"
            mock_session.get.assert_called_once_with("/api/search", params={"type": "dash-db"})
    
    @pytest.mark.asyncio
    async def test_get_dashboard_success(self, session_manager, grafana_config):
        """Test getting a dashboard by UID"""
        server_id = "test_server"
        uid = "test_dashboard_uid"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "dashboard": {"uid": uid, "title": "Test Dashboard"},
            "meta": {"version": 1}
        }
        
        with patch.object(session_manager, 'get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_get_session.return_value = mock_session
            
            result = await session_manager.get_dashboard(server_id, grafana_config, uid)
            
            assert result["dashboard"]["uid"] == uid
            mock_session.get.assert_called_once_with(f"/api/dashboards/uid/{uid}")
    
    @pytest.mark.asyncio
    async def test_create_dashboard_success(self, session_manager, grafana_config):
        """Test creating a dashboard"""
        server_id = "test_server"
        dashboard = {"title": "New Dashboard", "panels": []}
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "uid": "new_uid",
            "status": "success",
            "version": 1
        }
        
        with patch.object(session_manager, 'get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_session.post = AsyncMock(return_value=mock_response)
            mock_get_session.return_value = mock_session
            
            result = await session_manager.create_dashboard(
                server_id, grafana_config, dashboard
            )
            
            assert result["uid"] == "new_uid"
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_delete_dashboard_success(self, session_manager, grafana_config):
        """Test deleting a dashboard"""
        server_id = "test_server"
        uid = "dashboard_to_delete"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "title": "Deleted Dashboard",
            "message": "Dashboard deleted"
        }
        
        with patch.object(session_manager, 'get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_session.delete = AsyncMock(return_value=mock_response)
            mock_get_session.return_value = mock_session
            
            result = await session_manager.delete_dashboard(
                server_id, grafana_config, uid
            )
            
            assert result["message"] == "Dashboard deleted"
            mock_session.delete.assert_called_once_with(f"/api/dashboards/uid/{uid}")
    
    @pytest.mark.asyncio
    async def test_search_dashboards_with_filters(self, session_manager, grafana_config):
        """Test searching dashboards with filters"""
        server_id = "test_server"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"uid": "dash1", "title": "Dashboard 1", "tags": ["test"]}
        ]
        
        with patch.object(session_manager, 'get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_get_session.return_value = mock_session
            
            result = await session_manager.search_dashboards(
                server_id, grafana_config, query="test", tags=["test"], limit=10
            )
            
            assert len(result) == 1
            assert result[0]["tags"] == ["test"]
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, session_manager, grafana_config):
        """Test connection test with successful response"""
        server_id = "test_server"
        
        health_response = MagicMock()
        health_response.status_code = 200
        health_response.json.return_value = {
            "version": "9.0.0",
            "database": "ok"
        }
        
        org_response = MagicMock()
        org_response.status_code = 200
        org_response.json.return_value = {"name": "Test Org"}
        
        with patch.object(session_manager, 'get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(side_effect=[health_response, org_response])
            mock_get_session.return_value = mock_session
            
            result = await session_manager.test_connection(server_id, grafana_config)
            
            assert result["connected"] is True
            assert result["status"] == "connected"
            assert result["version"] == "9.0.0"
            assert result["organization"] == "Test Org"
    
    @pytest.mark.asyncio
    async def test_test_connection_failure(self, session_manager, grafana_config):
        """Test connection test with failure"""
        server_id = "test_server"

        with patch.object(session_manager, 'get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(side_effect=Exception("Connection refused"))
            mock_get_session.return_value = mock_session

            result = await session_manager.test_connection(server_id, grafana_config)

            assert result["connected"] is False
            assert result["status"] == "error"
            assert "Connection refused" in result["error"]

    @pytest.mark.asyncio
    async def test_get_datasource_by_name_found(self, session_manager, grafana_config):
        """Test getting datasource by name when it exists"""
        server_id = "test_server"
        datasource_name = "Prometheus"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 1,
                "uid": "prometheus-uid",
                "name": "Prometheus",
                "type": "prometheus",
                "url": "http://prometheus:9090",
                "isDefault": True
            },
            {
                "id": 2,
                "uid": "loki-uid",
                "name": "Loki",
                "type": "loki",
                "url": "http://loki:3100",
                "isDefault": False
            }
        ]

        with patch.object(session_manager, 'get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_get_session.return_value = mock_session

            result = await session_manager.get_datasource_by_name(
                server_id, grafana_config, datasource_name
            )

            assert result["exists"] is True
            assert result["id"] == 1
            assert result["uid"] == "prometheus-uid"
            assert result["name"] == "Prometheus"
            assert result["type"] == "prometheus"
            assert result["isDefault"] is True

    @pytest.mark.asyncio
    async def test_get_datasource_by_name_not_found(self, session_manager, grafana_config):
        """Test getting datasource by name when it doesn't exist"""
        server_id = "test_server"
        datasource_name = "NonExistent"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 1,
                "uid": "prometheus-uid",
                "name": "Prometheus",
                "type": "prometheus"
            }
        ]

        with patch.object(session_manager, 'get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_get_session.return_value = mock_session

            result = await session_manager.get_datasource_by_name(
                server_id, grafana_config, datasource_name
            )

            assert result["exists"] is False
            assert result["name"] == datasource_name
            assert "not found" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_get_datasource_by_name_case_insensitive(
        self, session_manager, grafana_config
    ):
        """Test that datasource search is case-insensitive"""
        server_id = "test_server"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 1,
                "uid": "prometheus-uid",
                "name": "Prometheus",
                "type": "prometheus"
            }
        ]

        with patch.object(session_manager, 'get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_get_session.return_value = mock_session

            # Test with different case
            result = await session_manager.get_datasource_by_name(
                server_id, grafana_config, "prometheus"
            )

            assert result["exists"] is True
            assert result["name"] == "Prometheus"

