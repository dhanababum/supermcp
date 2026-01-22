from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class DatabricksConfig(BaseModel):
    """Configuration model for Databricks Connector"""

    server_hostname: str = Field(
        description="Databricks workspace server hostname (e.g., adb-1234567890123456.7.azuredatabricks.net)"
    )
    http_path: str = Field(
        description="HTTP path for SQL warehouse or compute (e.g., /sql/1.0/warehouses/abc123def456)"
    )
    access_token: str = Field(
        description="Personal access token for authentication"
    )
    catalog: Optional[str] = Field(
        default=None,
        description="Default catalog name (optional)"
    )
    default_schema: Optional[str] = Field(
        default=None,
        description="Default schema name (optional)"
    )
    warehouse_id: Optional[str] = Field(
        default=None,
        description="SQL warehouse ID (optional, for connection pooling)"
    )
    pool_size: int = Field(
        default=5,
        description="Connection pool size for SQL connections"
    )
    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates (set to False for self-signed certificates, not recommended for production)"
    )


class ExecuteQueryParams(BaseModel):
    """Parameters for executing a Databricks SQL query"""

    query: str = Field(description="SQL query to execute")
    params: Optional[List[Any]] = Field(
        default=None,
        description="Query parameters for parameterized queries (use ? placeholders)"
    )


class ListSchemasParams(BaseModel):
    """Parameters for listing schemas"""

    catalog_name: str = Field(description="Catalog name to list schemas from")


class ListTablesParams(BaseModel):
    """Parameters for listing tables"""

    catalog_name: str = Field(description="Catalog name")
    schema_name: str = Field(description="Schema name")


class GetTableSchemaParams(BaseModel):
    """Parameters for getting table schema"""

    catalog_name: str = Field(description="Catalog name")
    schema_name: str = Field(description="Schema name")
    table_name: str = Field(description="Table name")


class ListVolumesParams(BaseModel):
    """Parameters for listing volumes"""

    catalog_name: str = Field(description="Catalog name")
    schema_name: str = Field(description="Schema name")


class GetVolumeInfoParams(BaseModel):
    """Parameters for getting volume information"""

    catalog_name: str = Field(description="Catalog name")
    schema_name: str = Field(description="Schema name")
    volume_name: str = Field(description="Volume name")


class ListTableDataParams(BaseModel):
    """Parameters for listing table data"""

    catalog_name: str = Field(description="Catalog name")
    schema_name: str = Field(description="Schema name")
    table_name: str = Field(description="Table name")
    limit: int = Field(default=100, description="Maximum number of rows to return")
    offset: int = Field(default=0, description="Offset for pagination")


class ListVolumeDataParams(BaseModel):
    """Parameters for listing volume data/files"""

    catalog_name: str = Field(description="Catalog name")
    schema_name: str = Field(description="Schema name")
    volume_name: str = Field(description="Volume name")
    path: Optional[str] = Field(
        default=None,
        description="Path within the volume (optional, defaults to root)"
    )
