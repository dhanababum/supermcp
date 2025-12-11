from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class DatabaseType(str, Enum):
    """Supported database types"""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MSSQL = "mssql"
    ORACLE = "oracle"
    SNOWFLAKE = "snowflake"
    DATABRICKS = "databricks"
    MARIADB = "mariadb"


class TenantSqlDbConfig(BaseModel):
    """Configuration model for Tenant SQL Database Connector"""

    db_type: DatabaseType = Field(
        description="The type of database (sqlite, postgresql, mysql, mssql, oracle, snowflake)"
    )
    host: Optional[str] = Field(
        default=None, description="Database host (not required for SQLite)"
    )
    port: Optional[int] = Field(
        default=None, description="Database port (uses default port if not specified)"
    )
    database: str = Field(description="Database name or file path (for SQLite)")
    username: Optional[str] = Field(
        default=None, description="Database username (not required for SQLite)"
    )
    password: Optional[str] = Field(
        default=None, description="Database password (not required for SQLite)"
    )
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Maximum overflow connections")
    additional_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional database-specific parameters (e.g., driver, warehouse for Snowflake)",
    )
    db_name: Optional[str] = Field(
        default="default",
        description="Identifier for this database instance (for multi-db support)"
    )


class ExecuteQueryParams(BaseModel):
    """Parameters for executing a SQL query"""

    query: str = Field(description="SQL query to execute")
    params: Optional[Dict[str, Any]] = Field(
        default=None, description="Query parameters for parameterized queries"
    )


class GetTableSchemaParams(BaseModel):
    """Parameters for getting table schema"""

    table_name: str = Field(description="Name of the table to inspect")


class SelectQueryTemplate(BaseModel):
    """Template for SELECT queries"""

    sql_query: str = Field(description="write your query here")
    limit: int = Field(description="this limits the table results", default=2)


class InsertQueryTemplate(BaseModel):
    """Template for INSERT queries"""

    table_name: str = Field(description="Table name to insert into")
    columns: str = Field(description="Column names (comma-separated)")
    values: str = Field(
        description="Values to insert (comma-separated, use :param_name for parameters)"
    )
