from mcp_pkg.dynamic_mcp import create_dynamic_mcp
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


mcp, mcp_app, app = create_dynamic_mcp(
    name="sql_db",
    config=CustomQueryConnector,
    version="1.0.0",
    logo_file_path="media/sqldb.png",
)


@mcp.tool()
def get_sql_db_config(num: int) -> str:
    return f"Hello, {num}!"


@mcp.template(name="get_sql_db_config", params_model=GetSqlDbConfigTemplate)
def get_sql_db_config_template(params: GetSqlDbConfigTemplate) -> str:
    return f"Hello, {params.num}!"


@mcp.template(name="select_query", params_model=SelectQueryTemplate)
def select_query_template(params: SelectQueryTemplate, **kwargs) -> str:
    return params.query.format(**kwargs)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("cc:app", host="0.0.0.0", port=8025, reload=True)
