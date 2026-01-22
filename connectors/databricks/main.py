"""Databricks MCP Connector - Main Entry Point"""

from mcp_pkg.dynamic_mcp import (
    create_dynamic_mcp,
    get_current_server_id,
    get_current_server_config
)
from typing import Dict, Any, List
import os
import logging
import asyncio

from schema import (
    DatabricksConfig,
    ExecuteQueryParams,
    ListSchemasParams,
    ListTablesParams,
    GetTableSchemaParams,
    ListVolumesParams,
    GetVolumeInfoParams,
    ListTableDataParams,
    ListVolumeDataParams,
)
from db_manager import ConnectionManager


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


mcp, app = create_dynamic_mcp(
    name="databricks",
    config=DatabricksConfig,
    version="1.0.0",
    logo_file_path=os.path.join(
        os.path.dirname(__file__), "media/databricks-48.png"),
    stateless_http=True,
)

ui_schema = {
    "server_hostname": {
        "ui:widget": "text",
        "ui:placeholder": "adb-1234567890123456.7.azuredatabricks.net",
        "ui:help": "Databricks workspace server hostname",
    },
    "http_path": {
        "ui:widget": "text",
        "ui:placeholder": "/sql/1.0/warehouses/abc123def456",
        "ui:help": "HTTP path for SQL warehouse or compute",
    },
    "access_token": {
        "ui:widget": "password",
        "ui:help": "Personal access token for authentication",
    },
    "catalog": {
        "ui:widget": "text",
        "ui:placeholder": "main",
        "ui:help": "Default catalog name (optional)",
    },
    "default_schema": {
        "ui:widget": "text",
        "ui:placeholder": "default",
        "ui:help": "Default schema name (optional)",
    },
    "warehouse_id": {
        "ui:widget": "text",
        "ui:placeholder": "abc123def456",
        "ui:help": "SQL warehouse ID (optional)",
    },
    "pool_size": {
        "ui:widget": "updown",
        "ui:help": "Connection pool size for SQL connections",
    },
    "verify_ssl": {
        "ui:widget": "checkbox",
        "ui:help": "Verify SSL certificates (uncheck only for self-signed certs, not recommended for production)",
    },
}
mcp.register_ui_schema(ui_schema)

connection_manager: ConnectionManager = ConnectionManager()
asyncio.ensure_future(connection_manager.cleanup_loop())


@mcp.on_server_create()
async def on_server_start(server_id: str, server_config: DatabricksConfig):
    """Initialize Databricks connections when MCP server starts"""
    try:
        logger.info(
            f"Initializing Databricks connection for {server_config.server_hostname}"
        )
        await connection_manager.test_connection(server_id, server_config)
        
        catalog = server_config.catalog or "main"
        schema = server_config.default_schema or "default"
        
        logger.info(
            f"Databricks connection established successfully "
            f"(catalog: {catalog}, schema: {schema})"
        )
    except Exception as e:
        logger.error(f"Failed to initialize Databricks connection: {str(e)}")
        raise


@mcp.on_server_destroy()
async def on_server_stop():
    """Cleanup Databricks connections when MCP server stops"""
    server_id = get_current_server_id()
    await connection_manager.close_connection(server_id)
    logger.info(f"Closing Databricks connection for server {server_id}")


@mcp.tool()
async def list_catalogs() -> List[Dict[str, Any]]:
    """
    List all Unity Catalog catalogs visible to the user.
    
    Returns:
        List of catalogs with name, owner, comment, and other metadata
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(f"Listing catalogs for server {server_id}")
    return await connection_manager.list_catalogs(server_id, server_config)


@mcp.tool()
async def list_schemas(catalog_name: str) -> List[Dict[str, Any]]:
    """
    List schemas in a specific Unity Catalog catalog.
    
    Args:
        catalog_name: Name of the catalog to list schemas from
    
    Returns:
        List of schemas with name, full_name, owner, and other metadata
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(f"Listing schemas in catalog {catalog_name} for server {server_id}")
    return await connection_manager.list_schemas(server_id, server_config, catalog_name)


@mcp.tool()
async def list_tables(catalog_name: str, schema_name: str) -> List[Dict[str, Any]]:
    """
    List tables in a specific catalog.schema.
    
    Args:
        catalog_name: Name of the catalog
        schema_name: Name of the schema
    
    Returns:
        List of tables with name, full_name, table_type, and other metadata
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(
        f"Listing tables in {catalog_name}.{schema_name} for server {server_id}"
    )
    return await connection_manager.list_tables(
        server_id, server_config, catalog_name, schema_name
    )


@mcp.tool()
async def get_table_schema(
    catalog_name: str, schema_name: str, table_name: str
) -> Dict[str, Any]:
    """
    Get detailed schema information for a specific table.
    
    Args:
        catalog_name: Name of the catalog
        schema_name: Name of the schema
        table_name: Name of the table
    
    Returns:
        Dictionary with table schema including columns, types, and metadata
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(
        f"Getting schema for {catalog_name}.{schema_name}.{table_name} "
        f"for server {server_id}"
    )
    return await connection_manager.get_table_schema(
        server_id, server_config, catalog_name, schema_name, table_name
    )


@mcp.tool()
async def list_volumes(catalog_name: str, schema_name: str) -> List[Dict[str, Any]]:
    """
    List volumes in a specific catalog.schema.
    
    Args:
        catalog_name: Name of the catalog
        schema_name: Name of the schema
    
    Returns:
        List of volumes with name, full_name, volume_type, and other metadata
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(
        f"Listing volumes in {catalog_name}.{schema_name} for server {server_id}"
    )
    return await connection_manager.list_volumes(
        server_id, server_config, catalog_name, schema_name
    )


@mcp.tool()
async def get_volume_info(
    catalog_name: str, schema_name: str, volume_name: str
) -> Dict[str, Any]:
    """
    Get detailed information about a specific volume.
    
    Args:
        catalog_name: Name of the catalog
        schema_name: Name of the schema
        volume_name: Name of the volume
    
    Returns:
        Dictionary with volume information including storage_location and metadata
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(
        f"Getting info for volume {catalog_name}.{schema_name}.{volume_name} "
        f"for server {server_id}"
    )
    return await connection_manager.get_volume_info(
        server_id, server_config, catalog_name, schema_name, volume_name
    )


@mcp.tool()
async def execute_query(
    query: str, params: List[Any] | None = None
) -> List[Dict[str, Any]]:
    """
    Execute a SQL query against Databricks SQL warehouse.
    
    This tool allows you to execute any SQL query (SELECT, INSERT, UPDATE, DELETE, etc.)
    with support for parameterized queries to prevent SQL injection.
    
    Args:
        query: SQL query to execute
        params: Optional list of parameters for parameterized queries (use ? placeholders)
    
    Returns:
        For SELECT queries: List of dictionaries representing rows
        For INSERT/UPDATE/DELETE: List with affected_rows count
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    validated = ExecuteQueryParams(query=query, params=params)
    logger.info(f"Executing query for server {server_id}")
    return await connection_manager.execute_query(
        server_id, server_config, validated.query, validated.params
    )


@mcp.tool()
async def list_table_data(
    catalog_name: str,
    schema_name: str,
    table_name: str,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    List data from a table with pagination support.
    
    Args:
        catalog_name: Name of the catalog
        schema_name: Name of the schema
        table_name: Name of the table
        limit: Maximum number of rows to return (default: 100)
        offset: Offset for pagination (default: 0)
    
    Returns:
        Dictionary with rows, count, limit, and offset
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(
        f"Listing data from {catalog_name}.{schema_name}.{table_name} "
        f"for server {server_id}"
    )
    return await connection_manager.list_table_data(
        server_id, server_config, catalog_name, schema_name, table_name, limit, offset
    )


@mcp.tool()
async def list_volume_data(
    catalog_name: str,
    schema_name: str,
    volume_name: str,
    path: str | None = None
) -> List[Dict[str, Any]]:
    """
    List files/data in a volume (directory listing).
    
    Args:
        catalog_name: Name of the catalog
        schema_name: Name of the schema
        volume_name: Name of the volume
        path: Optional path within the volume (defaults to root)
    
    Returns:
        List of files/directories in the volume
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(
        f"Listing data in volume {catalog_name}.{schema_name}.{volume_name} "
        f"for server {server_id}"
    )
    return await connection_manager.list_volume_data(
        server_id, server_config, catalog_name, schema_name, volume_name, path
    )


@mcp.tool()
async def test_connection() -> Dict[str, Any]:
    """
    Test the Databricks connection and return connection status information.
    
    This tool verifies that both SQL and WorkspaceClient connections are active
    and returns connection details.
    
    Returns:
        Dictionary with connection status, SQL connection status, and
        WorkspaceClient status
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(f"Testing connection for server {server_id}")
    return await connection_manager.test_connection(server_id, server_config)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8033")),
        reload=False,
        workers=int(os.getenv("WORKERS", "1")),
    )
