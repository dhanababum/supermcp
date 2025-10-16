import uuid
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, model_validator
from fastapi_users import schemas
from typing import Optional


class ConnectorMode(Enum):
    sync = "sync"
    active = "active"
    deactive = "deactive"


class ToolType(Enum):
    static = "static"
    dynamic = "dynamic"


class McpConnectorToolItem(BaseModel):
    name: str
    description: str | None = None
    inputSchema: dict = Field(default_factory=dict)
    model_config = ConfigDict(extra="allow")


class McpConnectorTemplateItem(BaseModel):
    name: str
    description: str
    properties: dict = Field(default_factory=dict)
    model_config = ConfigDict(extra="allow")


class McpServerToolItem(McpConnectorToolItem):
    model_config = ConfigDict(extra="allow")


class McpServerTemplateItem(McpConnectorTemplateItem):
    id: str
    is_active: bool = Field(default=True)
    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def update_id(cls, data: dict) -> dict:
        data["id"] = data["name"].replace("_", "-")
        return data


class UserRead(schemas.BaseUser[uuid.UUID]): ...


class UserCreate(schemas.BaseUserCreate): ...


class UserUpdate(schemas.BaseUserUpdate): ...


class RegisterRequest(BaseModel):
    name: str


class RegisterConnectorRequest(BaseModel):
    name: str
    description: str


class CreateConnectorRequest(BaseModel):
    connector_id: str  # ID of the registered connector to activate
    connector_url: str  # URL to fetch the connector schema from


class CreateToolFromTemplateRequest(BaseModel):
    connector_id: str
    template_name: str
    template_params: dict
    tool_name: str
    description: str


class AuthRequest(BaseModel):
    token: str


class GrantConnectorAccessRequest(BaseModel):
    user_id: uuid.UUID
    connector_id: int


class RevokeConnectorAccessRequest(BaseModel):
    user_id: uuid.UUID
    connector_id: int


class UpdateUserRoleRequest(BaseModel):
    is_superuser: bool
