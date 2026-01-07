"""Grafana MCP Connector - Main Entry Point"""

from mcp_pkg.dynamic_mcp import (
    create_dynamic_mcp,
    get_current_server_id,
    get_current_server_config
)
from typing import Dict, Any, Optional, List
import os
import logging
import json

from schema import (
    GrafanaConfig,
    CloneDashboardTemplate,
    BackupDashboardTemplate,
)
from session_manager import SessionManager


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create MCP server instance
mcp, app = create_dynamic_mcp(
    name="grafana",
    config=GrafanaConfig,
    version="1.0.0",
    logo_file_path=os.path.join(
        os.path.dirname(__file__),
        "media/grafana-48.png"),
    stateless_http=True,
)

# Register UI schema for form rendering
ui_schema = {
    "grafana_url": {
        "ui:widget": "text",
        "ui:placeholder": "https://grafana.example.com",
        "ui:help": "Full URL to your Grafana instance (including protocol)",
    },
    "auth_type": {
        "ui:widget": "radio",
        "ui:help": (
            "Authentication method "
            "(Service Account Token recommended for Grafana 9.0+)"
        ),
    },
    "service_account_token": {
        "ui:widget": "password",
        "ui:help": "Service account token for authentication (Grafana 9.0+)",
    },
    "api_key": {
        "ui:widget": "password",
        "ui:help": "API Key for authentication (legacy method)",
    },
    "verify_ssl": {
        "ui:widget": "checkbox",
        "ui:help": "Verify SSL certificates (recommended for production)",
    },
    "timeout": {
        "ui:widget": "updown",
        "ui:help": "Request timeout in seconds",
    },
    "additional_params": {
        "ui:widget": "textarea",
        "ui:options": {"rows": 4},
        "ui:placeholder": '{"X-Custom-Header": "value"}',
        "ui:help": "Additional HTTP headers as JSON object (optional)",
    },
}
mcp.register_ui_schema(ui_schema)

# Create session manager for HTTP connections
session_manager: SessionManager = SessionManager(
    global_max_sessions=100,
    per_target_max=10,
    idle_ttl=300
)
session_manager.cleanup_loop()


@mcp.on_server_create()
async def on_server_start(server_id: str, server_config: GrafanaConfig):
    """
    Initialize HTTP session when MCP server starts.
    This is called once when a server is created with specific configuration.
    """
    try:
        logger.info(
            f"Initializing Grafana connection for {server_config.grafana_url}"
        )
        
        # Pre-create session to validate configuration
        await session_manager.get_session(server_id, server_config)
        
        # Use db_name from config, default to "default"
        db_name = server_config.db_name or "default"
        
        logger.info(
            f"Grafana connection established successfully "
            f"for server: {db_name}"
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize Grafana connection: {str(e)}")
        raise


@mcp.on_server_destroy()
async def on_server_stop():
    """
    Cleanup HTTP session when MCP server stops.
    """
    server_id = get_current_server_id()
    await session_manager.close_session(server_id)
    logger.info(f"Closing Grafana connection for server {server_id}")


@mcp.tool()
async def list_dashboards() -> List[Dict[str, Any]]:
    """
    List all dashboards accessible to the authenticated user.
    
    Returns a list of dashboard summaries including:
    - uid: Dashboard unique identifier
    - title: Dashboard title
    - url: Dashboard URL
    - type: Resource type (dash-db)
    - tags: List of tags
    - isStarred: Whether dashboard is starred
    - folderId: Folder ID containing the dashboard
    - folderTitle: Folder title
    
    Returns:
        List of dashboard summary objects
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(f"Listing dashboards for server {server_id}")
    
    return await session_manager.list_dashboards(server_id, server_config)


@mcp.tool()
async def get_dashboard(uid: str) -> Dict[str, Any]:
    """
    Get a specific dashboard by its unique identifier (UID).
    
    Args:
        uid: Dashboard unique identifier
    
    Returns:
        Dashboard object containing:
        - dashboard: Full dashboard JSON model
        - meta: Dashboard metadata (version, created, updated, etc.)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(f"Getting dashboard {uid} for server {server_id}")
    
    return await session_manager.get_dashboard(server_id, server_config, uid)


@mcp.tool()
async def create_dashboard(
    dashboard: Dict[str, Any],
    folder_uid: Optional[str] = None,
    message: Optional[str] = None,
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    Create a new dashboard in Grafana.
    
    The dashboard object should contain at minimum:
    - title: Dashboard title
    - panels: List of panels (can be empty)
    
    Optional fields:
    - uid: Dashboard UID (will be auto-generated if not provided)
    - tags: List of tags
    - timezone: Timezone setting
    - schemaVersion: Schema version (defaults to latest)
    
    Args:
        dashboard: Dashboard JSON object
        folder_uid: UID of the folder to create dashboard in (optional)
        message: Commit message for dashboard creation (optional)
        overwrite: Whether to overwrite existing dashboard with same UID
    
    Returns:
        Response object containing:
        - uid: Created dashboard UID
        - url: Dashboard URL
        - status: Creation status
        - version: Dashboard version
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(f"Creating dashboard for server {server_id}")
    
    # Validate dashboard has required fields
    if "title" not in dashboard:
        raise ValueError("Dashboard must have a 'title' field")
    
    return await session_manager.create_dashboard(
        server_id, server_config, dashboard, folder_uid, message, overwrite
    )


@mcp.tool()
async def update_dashboard(
    dashboard: Dict[str, Any],
    overwrite: bool = True,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing dashboard.
    
    The dashboard object must include:
    - uid: Dashboard UID to update
    - title: Dashboard title
    - version: Current version number (for optimistic locking)
    
    Args:
        dashboard: Dashboard JSON object with updated content
        overwrite: Whether to overwrite the existing dashboard (default: True)
        message: Commit message for dashboard update (optional)
    
    Returns:
        Response object containing:
        - uid: Updated dashboard UID
        - url: Dashboard URL
        - status: Update status
        - version: New dashboard version
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(f"Updating dashboard for server {server_id}")
    
    # Validate dashboard has required fields
    if "uid" not in dashboard:
        raise ValueError("Dashboard must have a 'uid' field for updates")
    if "title" not in dashboard:
        raise ValueError("Dashboard must have a 'title' field")
    
    return await session_manager.update_dashboard(
        server_id, server_config, dashboard, overwrite, message
    )


@mcp.tool()
async def delete_dashboard(uid: str) -> Dict[str, Any]:
    """
    Delete a dashboard by its UID.
    
    This operation is permanent and cannot be undone.
    Consider backing up the dashboard before deletion.
    
    Args:
        uid: Dashboard UID to delete
    
    Returns:
        Response object containing:
        - title: Deleted dashboard title
        - message: Deletion confirmation message
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(f"Deleting dashboard {uid} for server {server_id}")
    
    return await session_manager.delete_dashboard(server_id, server_config, uid)


@mcp.tool()
async def search_dashboards(
    query: Optional[str] = None,
    tags: Optional[List[str]] = None,
    folder_ids: Optional[List[int]] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Search for dashboards with optional filters.
    
    Search can be performed by:
    - Query string (searches dashboard titles and tags)
    - Specific tags (returns dashboards with ANY of the tags)
    - Folder IDs (returns dashboards in specific folders)
    
    Args:
        query: Search query string (optional)
        tags: List of tags to filter by (optional)
        folder_ids: List of folder IDs to search in (optional)
        limit: Maximum number of results to return (default: 100)
    
    Returns:
        List of dashboard summary objects matching the search criteria
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(f"Searching dashboards for server {server_id}")
    
    return await session_manager.search_dashboards(
        server_id, server_config, query, tags, folder_ids, limit
    )


@mcp.tool()
async def get_dashboard_permissions(uid: str) -> List[Dict[str, Any]]:
    """
    Get permissions for a specific dashboard.
    
    Returns the access control list (ACL) for the dashboard,
    showing which users and teams have what level of access.
    
    Args:
        uid: Dashboard UID
    
    Returns:
        List of permission entries, each containing:
        - id: Permission entry ID
        - dashboardId: Dashboard ID
        - userId/teamId: User or team ID
        - permission: Permission level (1=View, 2=Edit, 4=Admin)
        - permissionName: Human-readable permission name
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(f"Getting permissions for dashboard {uid}")
    
    return await session_manager.get_dashboard_permissions(
        server_id, server_config, uid
    )


@mcp.tool()
async def get_datasource_by_name(name: str) -> Dict[str, Any]:
    """
    Get a datasource by name and return its ID and details.

    Searches for a datasource by name (case-insensitive) and returns
    its details including ID, UID, type, and URL. This is useful for
    referencing datasources in dashboards.

    Args:
        name: Name of the datasource to find

    Returns:
        Dictionary containing:
        - exists: Boolean indicating if datasource was found
        - id: Datasource numeric ID (if found)
        - uid: Datasource UID (if found)
        - name: Datasource name (if found)
        - type: Datasource type (e.g., "prometheus", "loki") (if found)
        - url: Datasource URL (if found)
        - isDefault: Whether this is the default datasource (if found)
        - message: Error message (if not found)

    Example:
        >>> get_datasource_by_name("Prometheus")
        {
            "exists": True,
            "id": 1,
            "uid": "prometheus-uid",
            "name": "Prometheus",
            "type": "prometheus",
            "url": "http://prometheus:9090",
            "isDefault": True
        }

        >>> get_datasource_by_name("NonExistent")
        {
            "exists": False,
            "name": "NonExistent",
            "message": "Datasource 'NonExistent' not found"
        }
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(f"Getting datasource by name '{name}' for server {server_id}")

    return await session_manager.get_datasource_by_name(
        server_id, server_config, name
    )


@mcp.tool()
async def test_connection() -> Dict[str, Any]:
    """
    Test the connection to Grafana and return status information.
    
    Verifies that:
    - The Grafana URL is accessible
    - Authentication credentials are valid
    - The API is responding correctly
    
    Returns:
        Dictionary with connection status including:
        - status: Connection status string
        - connected: Boolean indicating if connection is successful
        - grafana_url: The Grafana URL being connected to
        - auth_type: Authentication method being used
        - health: Health check data from Grafana
        - organization: Organization name
        - version: Grafana version
        - error: Error message (if connection failed)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(f"Testing connection for server {server_id}")
    
    return await session_manager.test_connection(server_id, server_config)


@mcp.template(name="clone_dashboard", params_model=CloneDashboardTemplate)
async def clone_dashboard(
    params: CloneDashboardTemplate, **kwargs
) -> str:
    """
    Clone an existing dashboard with modifications.
    
    This template:
    1. Retrieves the source dashboard
    2. Creates a copy with a new title
    3. Optionally moves it to a different folder
    4. Optionally adds/updates tags
    5. Removes the UID to create a new dashboard
    
    Args:
        params: CloneDashboardTemplate containing:
            - source_uid: UID of the dashboard to clone
            - new_title: Title for the cloned dashboard
            - folder_uid: Target folder UID (optional)
            - tags: Tags to add to the cloned dashboard (optional)
    
    Returns:
        JSON string with the created dashboard information
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    
    # Get source dashboard
    source = await session_manager.get_dashboard(
        server_id, server_config, params.source_uid
    )
    
    # Extract dashboard model
    cloned = source["dashboard"].copy()
    
    # Modify for cloning
    cloned["title"] = params.new_title
    cloned["uid"] = None  # Remove UID to create new dashboard
    cloned["id"] = None  # Remove ID
    cloned["version"] = 0  # Reset version
    
    # Update tags if provided
    if params.tags:
        cloned["tags"] = params.tags
    
    # Create the cloned dashboard
    result = await session_manager.create_dashboard(
        server_id,
        server_config,
        cloned,
        folder_uid=params.folder_uid,
        message=f"Cloned from {params.source_uid}"
    )
    
    return json.dumps(result, indent=2)


@mcp.template(name="backup_dashboard", params_model=BackupDashboardTemplate)
async def backup_dashboard(
    params: BackupDashboardTemplate, **kwargs
) -> str:
    """
    Export a dashboard as JSON for backup purposes.
    
    This template retrieves a dashboard and formats it for export,
    optionally including or excluding metadata like version numbers
    and timestamps.
    
    Args:
        params: BackupDashboardTemplate containing:
            - uid: UID of the dashboard to backup
            - include_metadata: Whether to include metadata (default: True)
    
    Returns:
        JSON string representation of the dashboard
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    
    # Get dashboard
    result = await session_manager.get_dashboard(
        server_id, server_config, params.uid
    )
    
    if params.include_metadata:
        # Return full response with metadata
        return json.dumps(result, indent=2)
    else:
        # Return just the dashboard model
        dashboard = result["dashboard"]
        # Clean up fields that shouldn't be in backups
        clean_dashboard = {
            k: v for k, v in dashboard.items()
            if k not in ["id", "version"]
        }
        return json.dumps(clean_dashboard, indent=2)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8029")),
        reload=False,
        workers=int(os.getenv("WORKERS", "1")),
    )

