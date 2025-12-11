from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class MSSQLConfig(BaseModel):
    """Configuration model for MSSQL/Azure SQL Database Connector"""

    host: Optional[str] = Field(
        default=None,
        description=(
            "Database host (e.g., localhost or "
            "server.database.windows.net for Azure)"
        )
    )
    port: Optional[int] = Field(
        default=1433,
        description="Database port (default: 1433 for MSSQL)"
    )
    database: str = Field(description="Database name")
    username: Optional[str] = Field(
        default=None, description="Database username"
    )
    password: Optional[str] = Field(
        default=None, description="Database password"
    )
    azure_auth: bool = Field(
        default=False,
        description="Use Azure SQL Database authentication settings"
    )
    encrypt: bool = Field(
        default=True,
        description=(
            "Use encrypted connection (recommended for Azure SQL)"
        )
    )
    trust_server_certificate: bool = Field(
        default=False,
        description=(
            "Trust server certificate (set to True for self-signed certs)"
        )
    )
    pool_size: int = Field(
        default=5, description="Connection pool size"
    )
    max_overflow: int = Field(
        default=10, description="Maximum overflow connections"
    )
    additional_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Additional database-specific parameters "
            "(e.g., connection timeout)"
        ),
    )
    db_name: Optional[str] = Field(
        default="default",
        description="Identifier for this database instance"
    )


class ExecuteQueryParams(BaseModel):
    """Parameters for executing a MSSQL query"""

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
        description=(
            "Values to insert "
            "(comma-separated, use :param_name for parameters)"
        )
    )
