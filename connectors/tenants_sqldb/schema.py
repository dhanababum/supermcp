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


class TenantSqlDbConfig(BaseModel):
    """Configuration model for Tenant SQL Database Connector"""
    
    db_type: DatabaseType = Field(
        description="The type of database (sqlite, postgresql, mysql, mssql, oracle, snowflake)"
    )
    host: Optional[str] = Field(
        default=None,
        description="Database host (not required for SQLite)"
    )
    port: Optional[int] = Field(
        default=None,
        description="Database port (uses default port if not specified)"
    )
    database: str = Field(
        description="Database name or file path (for SQLite)"
    )
    username: Optional[str] = Field(
        default=None,
        description="Database username (not required for SQLite)"
    )
    password: Optional[str] = Field(
        default=None,
        description="Database password (not required for SQLite)"
    )
    pool_size: int = Field(
        default=5,
        description="Connection pool size"
    )
    max_overflow: int = Field(
        default=10,
        description="Maximum overflow connections"
    )
    additional_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional database-specific parameters (e.g., driver, warehouse for Snowflake)"
    )
