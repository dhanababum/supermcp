from ast import List
import httpx
from fastmcp.server.middleware.middleware import (
    Middleware, MiddlewareContext, CallNext
)
from fastmcp.server.dependencies import get_access_token
from fastmcp.tools import Tool
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult, MCPTool
from mcp.types import TextContent

from .schema import AppServerTool, ToolType
from .config import settings


class CustomToolMiddleware(Middleware):
    """
    - on_list_tools: call_next returns the full tool list, we filter to include only tools
      whose names are prefixed by '<user>__'.
    - on_call_tool: ensure the requested tool name belongs to the caller (owner prefix match).
    """

    async def on_call_tool(
        self, context: MiddlewareContext, call_next: CallNext
    ):
        access_token = get_access_token()

        app_server_tool: AppServerTool = await self.get_tool_by_name(
            access_token.token, context.message.name)
        fastmcp_context = context.fastmcp_context.fastmcp
        if app_server_tool and app_server_tool.tool_type == ToolType.dynamic:
            result = fastmcp_context.render_template(
                name=app_server_tool.template_name,
                raw_params=app_server_tool.template_args,
                extra_kwargs=context.message.arguments
            )
            result = ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=result)])
            return result
        elif not app_server_tool:
            raise ToolError(
                f"Access denied to private tool: {context.message.name}")
        tool: MCPTool = await call_next(context)
        return tool

    async def on_list_tools(
        self, context: MiddlewareContext, call_next: CallNext
    ):
        access_token = get_access_token()
        online_tools: List[AppServerTool] = await self.get_active_tools(
            access_token.token)
        static_tools = set()
        server_tools = await call_next(context)
        new_tools = []
        for app_server_tool in online_tools:
            app_server_tool: AppServerTool = app_server_tool
            tool: MCPTool = app_server_tool.tool
            if app_server_tool.tool_type == ToolType.static:
                static_tools.add(tool.name)
            else:
                new_tool = Tool(
                    name=tool.name,
                    parameters=tool.inputSchema,
                    description=tool.description,
                    annotations=tool.annotations,
                    meta=tool.meta,
                )
                new_tools.append(new_tool)
        for tool in server_tools:
            if tool.name in static_tools:
                new_tools.append(tool)
        return new_tools

    async def get_active_tools(self, access_token: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.app_base_url}/api/tools",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            return [AppServerTool(**tool) for tool in response.json()]

    async def get_tool_by_name(self, access_token: str, tool_name: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.app_base_url}/api/tool?name={tool_name}",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            return AppServerTool(
                **response.json()) if response.status_code == 200 else None
