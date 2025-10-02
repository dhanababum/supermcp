from enum import Enum
import pydantic
from pydantic import Field, SecretStr


class ConnectionType(Enum):
    sqlite = "sqlite"
    postgres = "postgres"
    mysql = "mysql"
    mssql = "mssql"
    oracle = "oracle"
    snowflake = "snowflake"


class SqlDbSchema(pydantic.BaseModel):
    connection_type: ConnectionType
    username: str = Field(description="The username for the database connection")
    password: SecretStr = Field(description="The password for the database connection")
    host: str = Field(description="The host for the database connection")
    port: int = Field(description="The port for the database connection")
    database: str = Field(description="The database for the database connection")