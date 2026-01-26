from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class SnowflakeConfig(BaseModel):
    """Configuration model for Snowflake Connector"""

    account: str = Field(
        description="Snowflake account identifier (e.g., xy12345.us-east-1 or myorg-myaccount)"
    )
    user: str = Field(
        description="Snowflake username for authentication"
    )
    password: str = Field(
        description="Snowflake password for authentication"
    )
    warehouse: Optional[str] = Field(
        default=None,
        description="Snowflake compute warehouse name (e.g., COMPUTE_WH)"
    )
    database: Optional[str] = Field(
        default=None,
        description="Default database name (optional)"
    )
    schema_name: Optional[str] = Field(
        default=None,
        description="Default schema name (optional)"
    )
    role: Optional[str] = Field(
        default=None,
        description="Snowflake role for access control (optional)"
    )
    pool_size: int = Field(
        default=5,
        description="Connection pool size"
    )


class ExecuteQueryParams(BaseModel):
    """Parameters for executing a Snowflake SQL query"""

    query: str = Field(description="SQL query to execute")
    params: Optional[List[Any]] = Field(
        default=None,
        description="Query parameters for parameterized queries (use %s placeholders)"
    )


class ListSchemasParams(BaseModel):
    """Parameters for listing schemas"""

    database_name: str = Field(description="Database name to list schemas from")


class ListTablesParams(BaseModel):
    """Parameters for listing tables"""

    database_name: str = Field(description="Database name")
    schema_name: str = Field(description="Schema name")


class GetTableSchemaParams(BaseModel):
    """Parameters for getting table schema"""

    database_name: str = Field(description="Database name")
    schema_name: str = Field(description="Schema name")
    table_name: str = Field(description="Table name")


class ListTableDataParams(BaseModel):
    """Parameters for listing table data"""

    database_name: str = Field(description="Database name")
    schema_name: str = Field(description="Schema name")
    table_name: str = Field(description="Table name")
    limit: int = Field(default=100, description="Maximum number of rows to return")
    offset: int = Field(default=0, description="Offset for pagination")


class ListStagesParams(BaseModel):
    """Parameters for listing Snowflake stages"""

    database_name: str = Field(description="Database name")
    schema_name: str = Field(description="Schema name")
