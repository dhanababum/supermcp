import uuid

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlmodel import Field, SQLModel, Relationship
from src.datatypes import (
    McpConnectorToolItem,
    McpConnectorTemplateItem,
    McpServerToolItem,
)
from src.datatypes import ToolType, ConnectorMode

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import (
    Column,
    String,
    LargeBinary,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

UserBase = declarative_base()


class User(SQLAlchemyBaseUserTableUUID, UserBase):
    __tablename__ = "user"
    __table_args__ = {"extend_existing": True}


class McpConnector(SQLModel, AsyncAttrs, table=True):
    """
    Model for MCP Connector instances.
    """

    __tablename__ = "mcp_connectors"
    __table_args__ = {"extend_existing": True}

    id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True),
    )
    created_by: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            UUID(as_uuid=True), ForeignKey("user.id", use_alter=True)
        ),
        description="Foreign key to the superuser who created this connector",
    )
    name: str = Field(description="The connector name (e.g., 'sql_db')")
    url: str = Field(description="The connector URL")
    description: str = Field(description="The connector description")
    version: str = Field(description="The connector version")
    source_logo_url: bytes = Field(description="The connector logo")
    logo_name: str = Field(
        default="",
        sa_column=Column(String, nullable=False, server_default=""),
        description="The connector logo name",
    )
    mode: ConnectorMode = Field(
        default=ConnectorMode.sync,
        sa_column=Column(String(20), nullable=False, default="sync"),
        description="The connector mode",
    )
    secret: Optional[bytes] = Field(
        default=None,
        sa_column=Column(LargeBinary, nullable=True),
        description="The connector secret",
    )
    tools_config: List[McpConnectorToolItem] = Field(
        sa_column=Column(JSONB), description="The tools list as JSONB"
    )
    templates_config: List[McpConnectorTemplateItem] = Field(
        sa_column=Column(JSONB), description="The templates list as JSONB"
    )
    server_config: Dict[str, Any] = Field(
        sa_column=Column(JSONB), description="The server config as JSONB"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the connector was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the connector was last updated",
    )
    is_active: bool = Field(
        default=True,
        description="Whether this connector record is active (soft delete)",
    )

    # One-to-many relationship: one connector has many access records
    access_records: List["ConnectorAccess"] = Relationship(
        back_populates="connector"
    )
    servers: List["McpServer"] = Relationship(back_populates="connector")

    class Config:
        arbitrary_types_allowed = True


class ConnectorAccess(SQLModel, AsyncAttrs, table=True):
    """
    Model for managing user access to connectors.
    Only superusers can grant access to connectors.
    """

    __tablename__ = "connector_access"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    connector_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("mcp_connectors.id", ondelete="CASCADE"),
        ),
        description="Foreign key to the connector (CASCADE DELETE enabled)",
    )
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            UUID(as_uuid=True), ForeignKey("user.id", use_alter=True)
        ),
        description="Foreign key to the user who has access",
    )
    granted_by: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            UUID(as_uuid=True), ForeignKey("user.id", use_alter=True)
        ),
        description="Foreign key to the superuser who granted access",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When access was granted"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When access was last updated",
    )
    is_active: bool = Field(
        default=True, description="Whether this access is active"
    )

    # Many-to-one relationship: many access records belong to one connector
    connector: Optional[McpConnector] = Relationship(
        back_populates="access_records"
    )

    class Config:
        arbitrary_types_allowed = True


class McpServer(SQLModel, AsyncAttrs, table=True):
    """
    Model for MCP Server instances.
    One server can have multiple tokens (one-to-many relationship).
    """

    __tablename__ = "mcp_servers"
    __table_args__ = {"extend_existing": True}

    id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True),
    )
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            UUID(as_uuid=True), ForeignKey("user.id", use_alter=True)
        ),
        description="Foreign key to the user who owns this server",
    )
    connector_id: Optional[uuid.UUID] = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("mcp_connectors.id", ondelete="CASCADE"),
        ),
        description="Foreign key to the connector (CASCADE DELETE enabled)",
    )
    server_name: str = Field(description="The human-readable server name")
    server_url: Optional[str] = Field(
        default=None, description="The MCP server URL for connections"
    )
    configuration: dict = Field(
        sa_column=Column(JSONB), description="The dynamic server data as JSONB"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the server was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the server was last updated",
    )
    is_active: bool = Field(
        default=True, description="Whether this server is active"
    )

    connector: Optional[McpConnector] = Relationship(back_populates="servers")
    tokens: List["McpServerToken"] = Relationship(back_populates="server")
    server_tools: List["McpServerTool"] = Relationship(back_populates="server")

    class Config:
        arbitrary_types_allowed = True


class McpServerToken(SQLModel, AsyncAttrs, table=True):
    """
    Model for MCP Server tokens.
    Many tokens can belong to one server (many-to-one relationship).
    """

    __tablename__ = "mcp_server_tokens"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            UUID(as_uuid=True), ForeignKey("user.id", use_alter=True)
        ),
        description="Foreign key to the user who owns this token",
    )
    token: str = Field(description="The token for the MCP server")
    mcp_server_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("mcp_servers.id", ondelete="CASCADE"),
        ),
        description="Foreign key to the MCP server (CASCADE DELETE enabled)",
    )
    expires_at: Optional[datetime] = Field(
        default=None, description="When the token expires"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the token was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the token was last updated",
    )
    is_active: bool = Field(
        default=True, description="Whether this token is active"
    )
    server: Optional[McpServer] = Relationship(back_populates="tokens")

    class Config:
        arbitrary_types_allowed = True


class McpServerTool(SQLModel, AsyncAttrs, table=True):
    """
    Model for MCP Server tools.
    """

    __tablename__ = "mcp_server_tools"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            UUID(as_uuid=True), ForeignKey("user.id", use_alter=True)
        ),
        description="Foreign key to the user who owns this tool",
    )
    mcp_server_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("mcp_servers.id", ondelete="CASCADE"),
        ),
        description="Foreign key to the MCP server (CASCADE DELETE enabled)",
    )
    name: str = Field(description="The name of the tool")
    template_name: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True),
        description="The name of the template",
    )
    template_args: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="The template args as JSONB",
    )
    tool: McpServerToolItem = Field(
        sa_column=Column(JSONB), description="The tools as JSONB"
    )
    tool_type: ToolType = Field(description="The type of the tool")
    is_active: bool = Field(
        default=True, description="Whether this tool is active"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the tool was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the tool was last updated",
    )
    server: Optional[McpServer] = Relationship(back_populates="server_tools")

    class Config:
        arbitrary_types_allowed = True
