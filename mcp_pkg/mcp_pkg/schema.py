from pydantic import ConfigDict, BaseModel, PrivateAttr, Field
from typing import Callable, Any, Optional, Type, Dict
from enum import Enum

from fastmcp.tools.tool import MCPTool


class Template(BaseModel):
    name: str
    description: str
    inputSchema: dict | Type[BaseModel]
    title: str
    _key: str | None = PrivateAttr(default=None)

    def __init__(self, *, key: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._key = key

    @property
    def key(self) -> str:
        return self._key or self.name

    model_config = ConfigDict(extra="allow")


class ToolTemplate(Template):
    is_async: bool = False
    template_fn: Callable[..., Any]
    model_config = ConfigDict(extra="allow")


class ConnectorTemplate(BaseModel):
    name: str
    description: str
    version: str
    logo_url: str
    url: str
    config: Type[BaseModel] | dict
    tools: list[MCPTool]
    templates: list[Template]
    model_config = ConfigDict(extra="allow")


class ToolType(Enum):
    static = "static"
    dynamic = "dynamic"


class AppServerTool(BaseModel):
    tool_type: ToolType
    tool: MCPTool
    template_name: str | None = None
    template_args: dict | None = None
    model_config = ConfigDict(extra="allow")


class ConnectorConfig(BaseModel):
    params: Type[BaseModel] | dict
    ui_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="UI Schema hints for form rendering (RJSF uiSchema format)"
    )
    model_config = ConfigDict(extra="forbid")
