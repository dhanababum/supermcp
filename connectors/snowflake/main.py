"""Snowflake MCP Connector - Main Entry Point"""

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
    SnowflakeConfig,
    ExecuteQueryParams,
    ListSchemasParams,
    ListTablesParams,
    GetTableSchemaParams,
    ListTableDataParams,
    ListStagesParams,
)
from db_manager import ConnectionManager


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


mcp, app = create_dynamic_mcp(
    name="snowflake",
    config=SnowflakeConfig,
    version="1.0.0",
    logo_file_path=os.path.join(
        os.path.dirname(__file__), "media/snowflake-48.png"),
    stateless_http=True,
)

ui_schema = {
    "account": {
        "ui:widget": "text",
        "ui:placeholder": "xy12345.us-east-1",
        "ui:help": "Snowflake account identifier",
    },
    "user": {
        "ui:widget": "text",
        "ui:placeholder": "username",
        "ui:help": "Snowflake username for authentication",
    },
    "password": {
        "ui:widget": "password",
        "ui:help": "Snowflake password for authentication",
    },
    "warehouse": {
        "ui:widget": "text",
        "ui:placeholder": "COMPUTE_WH",
        "ui:help": "Snowflake compute warehouse name",
    },
    "database": {
        "ui:widget": "text",
        "ui:placeholder": "MY_DATABASE",
        "ui:help": "Default database name (optional)",
    },
    "schema_name": {
        "ui:widget": "text",
        "ui:placeholder": "PUBLIC",
        "ui:help": "Default schema name (optional)",
    },
    "role": {
        "ui:widget": "text",
        "ui:placeholder": "ACCOUNTADMIN",
        "ui:help": "Snowflake role for access control (optional)",
    },
    "pool_size": {
        "ui:widget": "updown",
        "ui:help": "Connection pool size",
    },
}
mcp.register_ui_schema(ui_schema)

connection_manager: ConnectionManager = ConnectionManager()
asyncio.ensure_future(connection_manager.cleanup_loop())


@mcp.on_server_create()
async def on_server_start(server_id: str, server_config: SnowflakeConfig):
    """Initialize Snowflake connections when MCP server starts"""
    try:
        logger.info(
            f"Initializing Snowflake connection for account {server_config.account}"
        )
        await connection_manager.test_connection(server_id, server_config)
        
        database = server_config.database or "N/A"
        schema = server_config.schema_name or "N/A"
        
        logger.info(
            f"Snowflake connection established successfully "
            f"(database: {database}, schema: {schema})"
        )
    except Exception as e:
        logger.error(f"Failed to initialize Snowflake connection: {str(e)}")
        raise


@mcp.on_server_destroy()
async def on_server_stop():
    """Cleanup Snowflake connections when MCP server stops"""
    server_id = get_current_server_id()
    await connection_manager.close_connection(server_id)
    logger.info(f"Closing Snowflake connection for server {server_id}")


@mcp.tool()
async def list_databases() -> List[Dict[str, Any]]:
    """
    List all accessible databases in the Snowflake account.
    
    Returns:
        List of databases with name, owner, comment, and other metadata
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(f"Listing databases for server {server_id}")
    return await connection_manager.list_databases(server_id, server_config)


@mcp.tool()
async def list_schemas(database_name: str) -> List[Dict[str, Any]]:
    """
    List schemas in a specific database.
    
    Args:
        database_name: Name of the database to list schemas from
    
    Returns:
        List of schemas with name, owner, and other metadata
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(f"Listing schemas in database {database_name} for server {server_id}")
    return await connection_manager.list_schemas(server_id, server_config, database_name)


@mcp.tool()
async def list_tables(database_name: str, schema_name: str) -> List[Dict[str, Any]]:
    """
    List tables in a specific database.schema.
    
    Args:
        database_name: Name of the database
        schema_name: Name of the schema
    
    Returns:
        List of tables with name, kind, owner, rows count, and other metadata
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(
        f"Listing tables in {database_name}.{schema_name} for server {server_id}"
    )
    return await connection_manager.list_tables(
        server_id, server_config, database_name, schema_name
    )


@mcp.tool()
async def get_table_schema(
    database_name: str, schema_name: str, table_name: str
) -> Dict[str, Any]:
    """
    Get detailed schema information for a specific table.
    
    Args:
        database_name: Name of the database
        schema_name: Name of the schema
        table_name: Name of the table
    
    Returns:
        Dictionary with table schema including columns, types, and metadata
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(
        f"Getting schema for {database_name}.{schema_name}.{table_name} "
        f"for server {server_id}"
    )
    return await connection_manager.get_table_schema(
        server_id, server_config, database_name, schema_name, table_name
    )


@mcp.tool()
async def list_warehouses() -> List[Dict[str, Any]]:
    """
    List all accessible warehouses in the Snowflake account.
    
    Returns:
        List of warehouses with name, state, size, type, and other metadata
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(f"Listing warehouses for server {server_id}")
    return await connection_manager.list_warehouses(server_id, server_config)


@mcp.tool()
async def list_stages(database_name: str, schema_name: str) -> List[Dict[str, Any]]:
    """
    List stages in a specific database.schema.
    
    Args:
        database_name: Name of the database
        schema_name: Name of the schema
    
    Returns:
        List of stages with name, url, type, and other metadata
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(
        f"Listing stages in {database_name}.{schema_name} for server {server_id}"
    )
    return await connection_manager.list_stages(
        server_id, server_config, database_name, schema_name
    )


@mcp.tool()
async def execute_query(
    query: str, params: List[Any] | None = None
) -> List[Dict[str, Any]]:
    """
    Execute a SQL query against Snowflake.
    
    This tool allows you to execute any SQL query (SELECT, INSERT, UPDATE, DELETE, etc.)
    with support for parameterized queries to prevent SQL injection.
    
    Args:
        query: SQL query to execute
        params: Optional list of parameters for parameterized queries (use %s placeholders)
    
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
    database_name: str,
    schema_name: str,
    table_name: str,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    List data from a table with pagination support.
    
    Args:
        database_name: Name of the database
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
        f"Listing data from {database_name}.{schema_name}.{table_name} "
        f"for server {server_id}"
    )
    return await connection_manager.list_table_data(
        server_id, server_config, database_name, schema_name, table_name, limit, offset
    )


@mcp.tool()
async def test_connection() -> Dict[str, Any]:
    """
    Test the Snowflake connection and return connection status information.
    
    This tool verifies that the connection is active and returns connection details
    including version, account, user, warehouse, database, schema, and role.
    
    Returns:
        Dictionary with connection status and Snowflake session information
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
        port=int(os.getenv("PORT", "8034")),
        reload=False,
        workers=int(os.getenv("WORKERS", "1")),
    )
