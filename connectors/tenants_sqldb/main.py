"""Tenants SQL Database MCP Connector - Main Entry Point"""
import json
from mcp_pkg.dynamic_mcp import create_dynamic_mcp, get_current_server_config, get_current_server_id
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os
import logging

from schema import TenantSqlDbConfig
from db_manager import DatabaseConnectionManager, DatabaseType


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration

class ExecuteQueryParams(BaseModel):
    """Parameters for executing a SQL query"""
    query: str = Field(description="SQL query to execute")
    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Query parameters for parameterized queries"
    )


class GetTableSchemaParams(BaseModel):
    """Parameters for getting table schema"""
    table_name: str = Field(description="Name of the table to inspect")


class SelectQueryTemplate(BaseModel):
    """Template for SELECT queries"""
    table_name: str = Field(description="Table name to query")
    columns: str = Field(default="*", description="Columns to select (comma-separated)")
    where_clause: Optional[str] = Field(default=None, description="WHERE clause (without WHERE keyword)")
    limit: Optional[int] = Field(default=None, description="Limit number of results")


class InsertQueryTemplate(BaseModel):
    """Template for INSERT queries"""
    table_name: str = Field(description="Table name to insert into")
    columns: str = Field(description="Column names (comma-separated)")
    values: str = Field(description="Values to insert (comma-separated, use :param_name for parameters)")


# Create MCP server instance
mcp, app = create_dynamic_mcp(
    name="tenants_sqldb",
    config=TenantSqlDbConfig,
    version="1.0.0",
    logo_file_path=os.path.join(os.path.dirname(__file__), "logo.png"),
)

dbs = {}


@mcp.on_server_create()
async def on_server_start(config: TenantSqlDbConfig):
    """
    Initialize database connection when MCP server starts.
    This is called once when a server is created with specific configuration.
    """
    server_id = get_current_server_id()
    server_config: TenantSqlDbConfig = get_current_server_config(
        app, server_id)
    
    try:
        logger.info(
            f"Initializing database connection for {server_config.db_type}")
        
        db_manager = DatabaseConnectionManager(
            db_type=config.db_type,
            host=config.host,
            port=config.port,
            database=server_config.database,
            username=server_config.username,
            password=server_config.password,
            additional_params=server_config.additional_params,
            pool_size=server_config.pool_size,
            max_overflow=server_config.max_overflow,
        )
        
        # Establish connection
        db_manager.connect()
        dbs[server_id] = db_manager
        
        logger.info(f"Database connection established successfully for {config.db_type}")
        
    except Exception as e:
        logger.error(f"Failed to initialize database connection: {str(e)}")
        raise


@mcp.on_server_destroy()
async def on_server_stop():
    """
    Cleanup database connection when MCP server stops.
    """
    server_id = get_current_server_id()
    db_manager = dbs[server_id]
    
    try:
        logger.info("Closing database connection")
        db_manager.disconnect()
        del dbs[server_id]
    except Exception as e:
        logger.error(f"Error during database disconnect: {str(e)}")


# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool()
def list_tables() -> str:
    """
    List all tables in the database.
    """
    server_id = get_current_server_id()
    db_manager: DatabaseConnectionManager = dbs[server_id]
    return db_manager.get_tables()


@mcp.tool()
def get_table_schema(table_name: str) -> str:
    """
    Get schema information for a specific table.
    
    Args:
        table_name: Name of the table to inspect
    
    Returns:
        JSON string with table schema information
    """
    server_id = get_current_server_id()
    db_manager: DatabaseConnectionManager = dbs[server_id]
    return json.dumps(db_manager.get_table_schema(table_name))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8026, reload=True)
