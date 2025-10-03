from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel, Relationship


class McpServer(SQLModel, table=True):
    """
    Model for MCP Server instances.
    One server can have multiple tokens (one-to-many relationship).
    """
    __tablename__ = "mcp_servers"

    id: Optional[int] = Field(default=None, primary_key=True)
    connector_name: str = Field(description="The connector name (e.g., 'sql_db')")
    server_name: str = Field(description="The human-readable server name")
    configuration: dict = Field(sa_column=Column(JSONB), description="The dynamic server data as JSONB")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the server was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the server was last updated")
    is_active: bool = Field(default=True, description="Whether this server is active")

    # One-to-many relationship: one server has many tokens
    tokens: List["McpServerToken"] = Relationship(back_populates="server")

    # One-to-many relationship: one server has many tools
    tools: List["McpServerTool"] = Relationship(back_populates="server")

    class Config:
        arbitrary_types_allowed = True


class McpServerToken(SQLModel, table=True):
    """
    Model for MCP Server tokens.
    Many tokens can belong to one server (many-to-one relationship).
    """
    __tablename__ = "mcp_server_tokens"
    
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
    
    id: Optional[int] = Field(default=None, primary_key=True)
    mcp_server_id: Optional[int] = Field(
        default=None,
        foreign_key="mcp_servers.id",
        description="Foreign key to the MCP server"
    )
    tool_name: str = Field(description="The tool name")
    tool_title: str = Field(description="The tool title")
    tool_description: str = Field(description="The tool description")
    tool_input_schema: dict = Field(sa_column=Column(JSONB), description="The tool input schema")
    tool_output_schema: dict = Field(sa_column=Column(JSONB), description="The tool output schema")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the tool was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the tool was last updated")
    is_active: bool = Field(default=True, description="Whether this tool is active")

    # Many-to-one relationship: many tools belong to one server
    server: Optional[McpServer] = Relationship(back_populates="tools")

    class Config:
        arbitrary_types_allowed = True
