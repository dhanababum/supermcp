from typing import Any
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator
from typing_extensions import Self


class ToolType(Enum):
    static = "static"
    dynamic = "dynamic"


class McpConnectorToolItem(BaseModel):
    name: str
    description: str
    inputSchema: dict = Field(default_factory=dict)
    model_config = ConfigDict(extra="allow")


class McpConnectorTemplateItem(BaseModel):
    name: str
    description: str
    properties: dict = Field(default_factory=dict)
    model_config = ConfigDict(extra="allow")


class McpServerToolItem(McpConnectorToolItem):
    id: str
    is_active: bool = Field(default=True)
    tool_type: ToolType = Field(default=ToolType.static)
    model_config = ConfigDict(extra="allow")

    @model_validator(mode='before')
    @classmethod
    def update_id(cls, data: dict) -> dict:
        data['id'] = data['name'].replace("_", "-")
        return data
    
    @field_serializer('tool_type')
    def serialize_items(self, items: ToolType) -> str:
        return items.value


class McpServerTemplateItem(McpConnectorTemplateItem):
    id: str
    is_active: bool = Field(default=True)
    model_config = ConfigDict(extra="allow")

    @model_validator(mode='before')
    @classmethod
    def update_id(cls, data: dict) -> dict:
        data['id'] = data['name'].replace("_", "-")
        return data
