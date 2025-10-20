from contextlib import asynccontextmanager
import inspect
from functools import partial
import os
import re
import threading
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_request
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount
import httpx
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse, JSONResponse

from .auth import CustomTokenVerifier, verify_token
from .middleware import CustomToolMiddleware
from .config import settings
from .schema import ConnectorTemplate, ConnectorConfig
from .template_registery import TemplateMixin
from typing import Callable, Optional, Type, List


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
    _server_create_hooks: List[Callable] = []
    _server_destroy_hooks: List[Callable] = []

    def __init__(self, *args, **kwargs):
        if "logo_file_path" in kwargs:
            self._logo_file_path = kwargs.pop("logo_file_path")
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
    
    def on_server_create(self, func: Optional[Callable] = None):
        """
        Decorator to register a callback for when a server is created.
        
        Usage:
            @mcp.on_server_create()
            async def handle_server_create(server_id: str, server_data: dict):
                print(f"Server {server_id} created!")
                # Initialize database connection for this server
        """
        def decorator(f: Callable) -> Callable:
            self._server_create_hooks.append(f)
            return f
        if func is None:
            return decorator
        else:
            return decorator(func)

    def on_server_destroy(self, func: Optional[Callable] = None):
        """
        Decorator to register a callback for when a server is destroyed.

        Usage:
            @mcp.on_server_destroy()
            async def handle_server_destroy(server_id: str):
                print(f"Server {server_id} destroyed!")
                # Cleanup database connection for this server
        """
        def decorator(f: Callable) -> Callable:
            self._server_destroy_hooks.append(f)
            return f

        if func is None:
            return decorator
        else:
            return decorator(func)

    async def _execute_create_hooks(self, server_id: str, server_data: dict):
        """Execute all registered server create hooks"""
        for hook in self._server_create_hooks:
            try:
                if inspect.iscoroutinefunction(hook):
                    await hook(server_id, server_data)
                else:
                    hook(server_id, server_data)
            except Exception as e:
                print(f"Error in server create hook: {e}")

    async def _execute_destroy_hooks(self, server_id: str):
        """Execute all registered server destroy hooks"""
        for hook in self._server_destroy_hooks:
            try:
                if inspect.iscoroutinefunction(hook):
                    await hook(server_id)
                else:
                    hook(server_id)
            except Exception as e:
                print(f"Error in server destroy hook: {e}")


async def create_mcp_servers_dictionary(
    app, mcp: DynamicMCP, mcp_app: Starlette
):
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            f"{settings.app_base_url}/api/connectors/"
            f"{settings.connector_id}/servers",
            headers={"Authorization": f"Bearer {settings.connector_secret}"}
        )
        online_servers = response.json()
        for key, server in online_servers.items():
            app.state.mcp_servers[key] = mcp._connector_config(**server)
            await mcp._execute_create_hooks(key, server)
            app.mount(f"/mcp/{key}", app=mcp_app, name=key)
            print(f"MCP app mounted for server {key}")
    return app.state.mcp_servers


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
        auth=CustomTokenVerifier(base_url=settings.app_base_url),
        logo_file_path=logo_file_path,
    )
    mcp.register_connector_config(config)
    
    # Keep the MCP app separate!
    mcp_app = mcp.http_app(
        path="/",
    )  # ← Renamed to mcp_app

    @mcp.custom_route("/data", methods=["GET"])
    async def get_mcp_data(request: Request):
        return JSONResponse({"message": "Hello, World!"})
    
    @asynccontextmanager
    async def custom_lifespan(app: Starlette):
        app.state.mcp_servers = {}
        await create_mcp_servers_dictionary(app, mcp, mcp_app)
        yield
        for server_id in list(app.state.mcp_servers.keys()):
            await mcp._execute_destroy_hooks(server_id)
            del app.state.mcp_servers[server_id]

    @asynccontextmanager
    async def combined_lifespan(app: Starlette):
        # Run both lifespans
        async with custom_lifespan(app):
            async with mcp_app.lifespan(app):
                yield
        # Create wrapper Starlette app
    app = Starlette(lifespan=combined_lifespan)

    mcp.add_middleware(
        CustomToolMiddleware(),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.app_web_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["mcp-session-id"]
    )

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

    async def get_logo(request: Request):
        return FileResponse(os.path.join(mcp._logo_file_path))

    async def create_new_mcp_server(request: Request):
        """Endpoint to dynamically create and mount a new server."""
        server_id = request.path_params["server_id"]
        await verify_token(request)
        if server_id in app.state.mcp_servers:
            return JSONResponse({"message": f"Server {server_id} already exists."})
        
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"{settings.app_base_url}/api/connectors/"
                f"{settings.connector_id}/servers/{server_id}",
                headers={"Authorization": f"Bearer {settings.connector_secret}"}
            )
            server_data = response.json()
            app.state.mcp_servers[server_id] = server_data
        
        await mcp._execute_create_hooks(server_id, server_data)
        
        # Mount the MCP app, not the wrapper app!
        app.mount(f"/mcp/{server_id}", mcp_app, name=server_id)  # ← Changed: mount mcp_app
        
        return JSONResponse({
            "message": f"Server {server_id} created and mounted at /mcp/{server_id}"
        })

    async def destroy_mcp_server(request: Request):
        server_id = request.path_params["server_id"]
        await verify_token(request)
        if server_id not in app.state.mcp_servers:
            return JSONResponse({"message": f"Server {server_id} does not exist."})
        
        await mcp._execute_destroy_hooks(server_id)
        del app.state.mcp_servers[server_id]
        
        for index, route in enumerate(app.routes):
            if isinstance(route, Mount) and route.path == f"/mcp/{server_id}":
                del app.routes[index]
                break
        
        return JSONResponse({"message": f"Server {server_id} destroyed"})

    app.add_route(
        path="/connector.json",
        methods=["GET"],
        route=get_tools,
    )
    app.add_route(
        path="/logo.png",
        methods=["GET"],
        route=get_logo,
    )
    app.add_route(
        path="/create-server/{server_id}",
        methods=["POST"],
        route=create_new_mcp_server,
    )
    app.add_route(
        path="/destroy-server/{server_id}",
        methods=["POST"],
        route=destroy_mcp_server,
    )
    print(app.routes)
    return mcp, app


def get_current_server_config(app: Starlette, server_id: str) -> str:
    return app.state.mcp_servers[server_id]


def get_current_server_id() -> str:
    try:
        request = get_http_request()
        path = request.url.path
        match = re.match(r'/mcp/([^/]+)', path)
        if match:
            return match.group(1)
        raise RuntimeError("Server ID not found in request path")
    except RuntimeError:
        raise RuntimeError("No HTTP request context")
