from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class Neo4jConfig(BaseModel):
    """Configuration model for Neo4j Database Connector"""

    uri: str = Field(
        description="Neo4j connection URI (e.g., bolt://localhost:7687 or neo4j://localhost:7687)"
    )
    username: Optional[str] = Field(
        default=None, description="Neo4j username for authentication"
    )
    password: Optional[str] = Field(
        default=None, description="Neo4j password for authentication"
    )
    database: str = Field(
        default="neo4j", description="Database name to connect to"
    )
    read_only: bool = Field(
        default=False,
        description="Enable read-only mode (disables write operations)"
    )
    db_name: Optional[str] = Field(
        default="default",
        description="Identifier for this database instance"
    )


class ReadCypherParams(BaseModel):
    """Parameters for executing a read Cypher query"""

    query: str = Field(description="Cypher query to execute")
    params: Optional[Dict[str, Any]] = Field(
        default=None, description="Query parameters for parameterized queries"
    )


class WriteCypherParams(BaseModel):
    """Parameters for executing a write Cypher query"""

    query: str = Field(description="Cypher query to execute")
    params: Optional[Dict[str, Any]] = Field(
        default=None, description="Query parameters for parameterized queries"
    )
