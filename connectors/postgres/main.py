"""Tenants SQL Database MCP Connector - Main Entry Point"""

from mcp_pkg.dynamic_mcp import (
    create_dynamic_mcp,
    get_current_server_id,
    get_current_server_config
)
from typing import Dict, Any
import os
import logging
import re

from schema import (
    SelectQueryTemplate,
    InsertQueryTemplate,
    ExecuteQueryParams,
    PostgresConfig,
)
from db_manager import PoolManager


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create MCP server instance
mcp, app = create_dynamic_mcp(
    name="postgresql",
    config=PostgresConfig,
    version="1.0.0",
    logo_file_path=os.path.join(
        os.path.dirname(__file__), "media/postgresql-48.png"),
)

# Register UI schema for form rendering
ui_schema = {
    "host": {
        "ui:widget": "text",
        "ui:placeholder": "localhost",
        "ui:help": "Database server hostname or IP address",
    },
    "port": {
        "ui:widget": "updown",
        "ui:help": "Database port (leave blank for default)",
    },
    "database": {
        "ui:placeholder": "my_database",
        "ui:help": "Name of the database to connect to",
    },
    "username": {
        "ui:widget": "text",
        "ui:placeholder": "db_user",
        "ui:help": "Database username for authentication",
    },
    "password": {
        "ui:widget": "password",
        "ui:help": "Database password (will be stored securely)",
    },
    "pool_size": {
        "ui:widget": "updown",
        "ui:help": "Number of persistent connections to maintain",
    },
    "max_overflow": {
        "ui:widget": "updown",
        "ui:help": "Maximum additional connections beyond pool_size",
    },
    "additional_params": {
        "ui:widget": "textarea",
        "ui:options": {"rows": 4},
        "ui:placeholder": '{"driver": "psycopg2", "ssl": true}',
        "ui:help": "Additional parameters as JSON object (optional)",
    },
}
mcp.register_ui_schema(ui_schema)

# Dictionary to store database connections per server
# Structure: Dict[server_id, DatabaseConnectionManager]
pool_manager: PoolManager = PoolManager()
pool_manager.cleanup_loop()


@mcp.on_server_create()
async def on_server_start(server_id: str, server_config: PostgresConfig):
    """
    Initialize database connection when MCP server starts.
    This is called once when a server is created with specific configuration.
    Supports multiple database instances per server using db_name identifier.
    """
    try:
        logger.info(
            f"Initializing database connection for {server_config.database}"
        )

        await pool_manager.get_pool(server_id, server_config)

        # Use db_name from config, default to "default"
        db_name = server_config.db_name or "default"

        logger.info(
            f"Database connection established successfully "
            f"for {server_config.db_type} (db_name: {db_name})"
        )

    except Exception as e:
        logger.error(f"Failed to initialize database connection: {str(e)}")
        raise


@mcp.on_server_destroy()
async def on_server_stop():
    """
    Cleanup database connection when MCP server stops.
    Handles multiple database instances per server.
    """
    server_id = get_current_server_id()
    await pool_manager.close_pool(server_id)
    logger.info(f"Closing database connection for server {server_id}")


@mcp.tool()
async def list_tables() -> list[str]:
    """
    List all tables in the database.

    Args:
        db_name: Identifier for the database instance (default: "default")
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(f"Listing tables for server {server_id}, db: {server_config.database}")

    return await pool_manager.get_tables(server_id, server_config)


@mcp.tool()
async def get_table_schema(
    table_name: str
) -> Dict[str, Any]:
    """
    Get schema information for a specific table.

    Args:
        table_name: Name of the table to inspect
        db_name: Identifier for the database instance (default: "default")

    Returns:
        JSON string with table schema information
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    _schema = await pool_manager.get_table_schema(
        server_id, server_config, table_name)
    return _schema


@mcp.tool()
async def execute_query(
    query: str, params: Dict[str, Any] | None = None
) -> list:
    """
    Execute a SQL query with optional parameters.

    This tool allows you to execute any SQL query
    (SELECT, INSERT, UPDATE, DELETE, etc.)
    with support for parameterized queries to prevent SQL injection.

    Args:
        query: SQL query to execute
        params: Optional dictionary of parameters for parameterized queries
        db_name: Identifier for the database instance (default: "default")

    Returns:
        For SELECT queries: List of dictionaries representing rows
        For INSERT/UPDATE/DELETE: List with affected_rows count
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    # Validate using ExecuteQueryParams for type safety
    validated = ExecuteQueryParams(query=query, params=params)
    return await pool_manager.execute_query(
        server_id, server_config, validated.query, validated.params)


@mcp.tool()
async def test_connection() -> Dict[str, Any]:
    """
    Test the database connection and return connection status information.

    This tool verifies that the database connection is active and returns
    connection details including database type, version, and pool
    configuration.

    Args:

    Returns:
        Dictionary with connection status, database information, and pool
        settings
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    logger.info(
        f"Testing connection for server {server_id}, db: {server_config.database}")
    return await pool_manager.test_connection(server_id, server_config)


@mcp.template(name="select_query", params_model=SelectQueryTemplate)
async def select_query(
    params: SelectQueryTemplate, **kwargs
) -> str:
    """
    Execute a SELECT query with optional limit.

    This template executes a SELECT query and limits the results.
    The query can include placeholders that will be replaced with kwargs.

    Args:
        params: SelectQueryTemplate containing:
            - sql_query: SQL SELECT query to execute (can include format
              placeholders)
            - limit: Maximum number of rows to return (default: 2)
        **kwargs: Additional parameters to format into the query

    Returns:
        JSON string representation of query results
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    # Format query with kwargs if provided
    formatted_query = (
        params.sql_query.format(**kwargs) if kwargs else params.sql_query
    )

    # Add LIMIT clause if not already present and limit is specified
    query_upper = formatted_query.upper().strip()
    if params.limit > 0 and "LIMIT" not in query_upper:
        # Check if query ends with semicolon
        if formatted_query.rstrip().endswith(";"):
            formatted_query = (
                formatted_query.rstrip()[:-1] +
                f" LIMIT {params.limit};"
            )
        else:
            formatted_query = (
                formatted_query.rstrip() + f" LIMIT {params.limit}"
            )

    results = await pool_manager.execute_query(
        server_id, server_config, formatted_query)
    return str(results)


@mcp.template(name="insert_query", params_model=InsertQueryTemplate)
async def insert_query(
    params: InsertQueryTemplate, **kwargs
) -> str:
    """
    Generate and execute an INSERT query.

    This template generates an INSERT INTO statement and executes it.
    Supports parameterized values using :param_name syntax.

    Args:
        params: InsertQueryTemplate containing:
            - table_name: Name of the table to insert into
            - columns: Comma-separated column names
            - values: Comma-separated values (can include :param_name
              placeholders)
        **kwargs: Additional parameters to substitute into the query

    Returns:
        JSON string representation of insertion result (affected_rows)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    # Build INSERT query
    values_list = [val.strip() for val in params.values.split(",")]

    # Build VALUES clause with placeholders
    values_placeholders = ", ".join(values_list)

    # Format the query with kwargs if provided
    formatted_values = (
        values_placeholders.format(**kwargs) if kwargs else values_placeholders
    )

    query = (
        f"INSERT INTO {params.table_name} ({params.columns}) "
        f"VALUES ({formatted_values})"
    )

    # Extract parameters from kwargs that match :param_name pattern
    param_pattern = r":(\w+)"
    param_names = re.findall(param_pattern, formatted_values)
    query_params = {
        name: kwargs.get(name)
        for name in param_names
        if name in kwargs
    }

    # Execute query with parameters
    results = await pool_manager.execute_query(
        server_id, server_config, query,
        query_params if query_params else None)
    return str(results)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8027")),
        reload=False, workers=int(os.getenv("WORKERS", "1")),
    )
