from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel, Relationship
from pydantic import model_validator
from datatypes import McpConnectorToolItem, McpConnectorTemplateItem, McpServerTemplateItem, McpServerToolItem


class McpConnector(SQLModel, table=True):
    """
    Model for MCP Connector instances.
    """
    __tablename__ = "mcp_connectors"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="The connector name (e.g., 'sql_db')")
    url: str = Field(description="The connector URL")
    description: str = Field(description="The connector description")
    version: str = Field(description="The connector version")
    source_logo_url: bytes = Field(description="The connector logo")
    logo_url: str = Field(description="The connector logo")
    tools_config: List[McpConnectorToolItem] = Field(sa_column=Column(JSONB), description="The tools list as JSONB")
    templates_config: List[McpConnectorTemplateItem] = Field(sa_column=Column(JSONB), description="The templates list as JSONB")
    server_config: Dict[str, Any] = Field(sa_column=Column(JSONB), description="The server config as JSONB")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the connector was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the connector was last updated")
    is_active: bool = Field(default=True, description="Whether this connector is active")

    class Config:
        arbitrary_types_allowed = True


class McpServer(SQLModel, table=True):
    """
    Model for MCP Server instances.
    One server can have multiple tokens (one-to-many relationship).
    """
    __tablename__ = "mcp_servers"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    connector_id: str = Field(description="The connector id (e.g., 'sql_db')")
    server_name: str = Field(description="The human-readable server name")
    configuration: dict = Field(sa_column=Column(JSONB), description="The dynamic server data as JSONB")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the server was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the server was last updated")
    is_active: bool = Field(default=True, description="Whether this server is active")
    # One-to-many relationship: one server has many tokens
    tokens: List["McpServerToken"] = Relationship(back_populates="server")

    # One-to-many relationship: one server has many tools
    server_tools: Optional["McpServerTool"] = Relationship(back_populates="server")

    class Config:
        arbitrary_types_allowed = True


class McpServerToken(SQLModel, table=True):
    """
    Model for MCP Server tokens.
    Many tokens can belong to one server (many-to-one relationship).
    """
    __tablename__ = "mcp_server_tokens"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(description="The token for the MCP server")
    mcp_server_id: Optional[int] = Field(
        default=None,
        foreign_key="mcp_servers.id",
        description="Foreign key to the MCP server"
    )
    expires_at: Optional[datetime] = Field(default=None, description="When the token expires")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the token was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the token was last updated")
    is_active: bool = Field(default=True, description="Whether this token is active")

    # Many-to-one relationship: many tokens belong to one server
    server: Optional[McpServer] = Relationship(back_populates="tokens")

    class Config:
        arbitrary_types_allowed = True


class McpServerTool(SQLModel, table=True):
    """
    Model for MCP Server tools.
    """
    __tablename__ = "mcp_server_tools"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    mcp_server_id: Optional[int] = Field(
        default=None,
        foreign_key="mcp_servers.id",
        description="Foreign key to the MCP server"
    )
    tools: List[McpServerToolItem] = Field(sa_column=Column(JSONB), description="The tools as JSONB")
    # Many-to-one relationship: many tools belong to one server
    server: Optional[McpServer] = Relationship(back_populates="server_tools")

    def get_tool(self, tool_id: str):
        for tool in self.tools:
            if tool.id == tool_id:
                return tool
        return None

    def get_tools(self, offset: int = 0, limit: int = 10):
        return [McpServerToolItem(**tool) for tool in self.tools[offset:offset+limit]]

    class Config:
        arbitrary_types_allowed = True
