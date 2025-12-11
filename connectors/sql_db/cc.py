from tarfile import data_filter
from mcp_pkg.dynamic_mcp import create_dynamic_mcp, get_current_server_id
from pydantic import BaseModel, Field
from enum import Enum
import os

os.environ["API_BASE_URL"] = "http://localhost:9001"
os.environ["API_WEB_URL"] = "http://localhost:3000"
os.environ["CONNECTOR_SECRET"] = "b6cb409aefdd4338bee0627a6a2c5243"
os.environ["CONNECTOR_ID"] = "5c91a05f-e9fa-4d8f-8903-b22c544f53aa"


class TypeConnection(Enum):
    sqlite = "sqlite"
    postgres = "postgres"
    mysql = "mysql"
    mssql = "mssql"
    oracle = "oracle"
    snowflake = "snowflake"


class CustomQueryConnector(BaseModel):
    """this is a connector for a custom query parameters"""
    type_connection: TypeConnection = Field(description="The type of the database connection")
    host: str = Field(description="The host for the database connection")


class GetSqlDbConfigTemplate(BaseModel):
    num: int = Field(description="The number to get the config for")


class SelectQueryTemplate(BaseModel):
    """this is a template for a select query"""
    query: str = Field(description="The query to execute")


mcp, app = create_dynamic_mcp(
    name="sql_db",
    config=CustomQueryConnector,
    version="1.0.0",
    logo_file_path="media/sqldb.png",
)


db_connections = {}


@mcp.on_server_create()
async def handle_server_created(server_id: str, server_data: dict):
    """Called when a new server is created"""
    print(f"🚀 Server {server_id} created! Initializing database...")
    print(f"Server data: {server_data}")
    db_type = server_data.get("type_connection", "sqlite")
    host = server_data.get("host", "localhost")
    try:
        db_connections[server_id] = {
            "type": db_type,
            "host": host,
            "status": "connected"
        }
        print(f"✅ Database initialized for server {server_id}")
    except Exception as e:
        print(f"❌ Failed to initialize database for {server_id}: {e}")


@mcp.on_server_destroy()
async def handle_server_destroyed(server_id: str):
    """Called when a server is destroyed"""
    print(f"🗑️  Server {server_id} destroyed! Cleaning up database...")

    if server_id in db_connections:
        try:
            del db_connections[server_id]
            print(f"✅ Database cleaned up for server {server_id}")
        except Exception as e:
            print(f"❌ Failed to cleanup database for {server_id}: {e}")


@mcp.tool()
def get_sql_db_config(num: int) -> str:
    server_id = get_current_server_id()
    print(db_connections[server_id])
    return f"Hello, {num}! Server ID: {server_id}"


@mcp.template(name="get_sql_db_config", params_model=GetSqlDbConfigTemplate)
def get_sql_db_config_template(params: GetSqlDbConfigTemplate) -> str:
    return f"Hello, {params.num}!"


@mcp.template(name="select_query", params_model=SelectQueryTemplate)
def select_query_template(params: SelectQueryTemplate, **kwargs) -> str:
    return params.query.format(**kwargs)


if __name__ == "__main__":
    import uvicorn
    # Pass the app object directly, not as a string
    uvicorn.run(app, host="0.0.0.0", port=8025, reload=False)
