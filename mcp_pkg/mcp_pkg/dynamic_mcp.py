import os
import threading
from fastapi import FastAPI, Request
from fastmcp import FastMCP

# from fastmcp.tools.tool import ParsedFunction
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse, JSONResponse
from .auth import CustomTokenVerifier
from .middleware import CustomToolMiddleware
from .config import settings
from .schema import ConnectorTemplate, ConnectorConfig
from .template_registery import TemplateMixin
from typing import Type


class DynamicMCP(FastMCP, TemplateMixin):
    """
    Dynamic MCP Server with template support.
    
    Combines FastMCP functionality with template registration capabilities.
    This allows you to:
    - Register tools using @mcp.tool (from FastMCP)
    - Register templates using @mcp.template (from TemplateMixin)
    - Dynamically render templates with validated parameters
    - Serve connector metadata including tools and templates
    
    Design Patterns:
    - Mixin Pattern: Combines FastMCP and TemplateMixin capabilities
    - Factory Pattern: Creates MCP servers with custom configurations
    - Template Method Pattern: Defines server setup workflow
    """
    
    _connector_config: Type[BaseModel] | None = None
    _logo_file_path: str | None = None

    def __init__(self, *args, **kwargs):
        if "logo_file_path" in kwargs:
            self._logo_file_path = kwargs.pop("logo_file_path")
        # Initialize template storage before calling super().__init__
        # to ensure TemplateMixin is properly initialized
        if not hasattr(self, '_templates'):
            self._templates = {}
        if not hasattr(self, '_registry_lock'):
            self._registry_lock = threading.Lock()
        super().__init__(*args, **kwargs)
    
    def register_connector_config(self, config: Type[BaseModel]):
        """Register the connector configuration schema"""
        self._connector_config = config

    def register_logo_file_path(self, logo_file_path: str):
        """Register the path to the connector logo"""
        self._logo_file_path = logo_file_path


def create_dynamic_mcp(
    name: str,
    config: BaseModel,
    version: str,
    logo_file_path: str,
):
    assert version is not None, "Version is required"
    assert config is not None, "Config is required"
    assert name is not None, "Name is required"
    assert logo_file_path is not None, "Logo file path is required"
    mcp = DynamicMCP(
        name=name,
        version=version,
        streamable_http_path="/",
        auth=CustomTokenVerifier(base_url=settings.app_base_url),
        logo_file_path=logo_file_path,
    )
    mcp.register_connector_config(config)
    mcp_app = mcp.http_app()
    mcp.add_middleware(
        CustomToolMiddleware(),
    )
    app = FastAPI(lifespan=mcp_app.lifespan)
    app.add_middleware(
        # CustomToolMiddleware(settings.app_base_url),
        CORSMiddleware,
        allow_origins=[settings.app_web_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["mcp-session-id"]
    )

    @app.get("/connector.json")
    async def get_tools(request: Request):
        host = request.headers.get("host")
        tools = await mcp.get_tools()
        templates = mcp.list_templates()
        tools_list = [
            tool.to_mcp_tool() for _, tool in tools.items()
        ]
        config = ConnectorConfig(
            params=mcp._connector_config.model_json_schema(),
        )
        data = ConnectorTemplate(
            name=mcp.name,
            description="Dynamic MCP",
            version=mcp.version,
            logo_url=app.url_path_for("get_logo"),
            url=f"http://{host}/connector.json",
            config=config.model_dump(),
            tools=tools_list,
            templates=templates,
        )
        return JSONResponse(data.model_dump())
   
    @app.get("/logo.png")
    async def get_logo(request: Request):
        return FileResponse(
            os.path.join(mcp._logo_file_path))
    # app.mount("/mcp", app=mcp_app)
    return mcp, mcp_app, app
