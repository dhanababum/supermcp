from ast import List
import asyncio
import time
import logging
import threading
from typing import Dict
import httpx
from fastmcp.server.middleware.middleware import Middleware, MiddlewareContext, CallNext
from fastmcp.server.dependencies import get_access_token, get_http_request
from fastmcp.tools import Tool
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult, MCPTool
from mcp.types import TextContent

from .schema import AppServerTool, ToolType
from .config import settings

logger = logging.getLogger(__name__)


class SessionStore:
    """Thread-safe in-memory store for tracking active MCP sessions."""
    
    def __init__(self, idle_timeout: int = 300):
        self._sessions: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self._idle_timeout = idle_timeout
    
    def update(self, session_id: str, user_id: str = None) -> None:
        """Update session with current timestamp."""
        if not session_id:
            return
        with self._lock:
            self._sessions[session_id] = {
                "last_seen": time.time(),
                "user_id": user_id,
            }
    
    def cleanup_stale(self) -> int:
        """Remove sessions that have been idle longer than timeout."""
        now = time.time()
        removed = 0
        with self._lock:
            stale = [
                sid for sid, data in self._sessions.items()
                if now - data["last_seen"] > self._idle_timeout
            ]
            for sid in stale:
                del self._sessions[sid]
                removed += 1
        return removed
    
    def get_active_count(self) -> int:
        """Return count of active sessions."""
        self.cleanup_stale()
        with self._lock:
            return len(self._sessions)
    
    def get_active_sessions(self) -> Dict[str, Dict]:
        """Return copy of all active sessions."""
        self.cleanup_stale()
        with self._lock:
            return dict(self._sessions)


# Global session store (shared across all servers in a connector)
_session_store = SessionStore(idle_timeout=300)


def get_session_id() -> str | None:
    """Extract session_id from MCP request headers."""
    try:
        request = get_http_request()
        return request.headers.get("mcp-session-id")
    except Exception:
        return None


class CustomToolMiddleware(Middleware):
    """
    - on_list_tools: call_next returns the full tool list, we filter to include only tools
      whose names are prefixed by '<user>__'.
    - on_call_tool: ensure the requested tool name belongs to the caller (owner prefix match).
    """

    async def on_call_tool(self, context: MiddlewareContext, call_next: CallNext):
        access_token = get_access_token()

        app_server_tool: AppServerTool = await self.get_tool_by_name(
            access_token.token, context.message.name
        )
        fastmcp_context = context.fastmcp_context.fastmcp
        if app_server_tool and app_server_tool.tool_type == ToolType.dynamic:
            is_async = fastmcp_context.get_template(
                app_server_tool.template_name
            ).is_async
            if is_async:
                result = await fastmcp_context.render_template_async(
                    name=app_server_tool.template_name,
                    raw_params=app_server_tool.template_args,
                    extra_kwargs=context.message.arguments,
                )
            else:
                result = fastmcp_context.render_template(
                    name=app_server_tool.template_name,
                    raw_params=app_server_tool.template_args,
                    extra_kwargs=context.message.arguments,
                )
            result = ToolResult(content=[TextContent(type="text", text=result)])
            return result
        elif not app_server_tool:
            raise ToolError(f"Access denied to private tool: {context.message.name}")
        tool: MCPTool = await call_next(context)
        return tool

    async def on_list_tools(self, context: MiddlewareContext, call_next: CallNext):
        # print headers
        access_token = get_access_token()
        online_tools: List[AppServerTool] = await self.get_active_tools(
            access_token.token
        )
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
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return [AppServerTool(**tool) for tool in response.json()]

    async def get_tool_by_name(self, access_token: str, tool_name: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.app_base_url}/api/tool?name={tool_name}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return (
                AppServerTool(**response.json())
                if response.status_code == 200
                else None
            )


class ObservabilityMiddleware(Middleware):
    """
    Middleware for logging tool calls and collecting metrics.
    Sends logs asynchronously to avoid blocking tool responses.
    """

    def __init__(
        self, 
        log_endpoint: str = None,
        max_result_len: int = 500,
        max_value_len: int = 500
    ):
        self.log_endpoint = log_endpoint or f"{settings.app_base_url}/api/logs"
        self.max_result_len = max_result_len
        self.max_value_len = max_value_len

    async def on_call_tool(self, context: MiddlewareContext, call_next: CallNext):
        start_time = time.perf_counter()
        tool_name = context.message.name
        arguments = context.message.arguments or {}

        try:
            access_token = get_access_token()
        except Exception:
            access_token = None

        session_id = get_session_id()

        tool_type = "static"
        if access_token:
            try:
                app_tool = await self._get_tool_info(access_token.token, tool_name)
                if app_tool:
                    tool_type = app_tool.tool_type.value if hasattr(app_tool.tool_type, 'value') else str(app_tool.tool_type)
            except Exception:
                pass

        try:
            result = await call_next(context)
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            result_summary = self._extract_result_summary(result, max_len=self.max_result_len)

            if access_token:
                asyncio.create_task(self._log_tool_call(
                    access_token=access_token.token,
                    tool_name=tool_name,
                    tool_type=tool_type,
                    arguments=self._truncate_dict(arguments, max_value_len=self.max_value_len),
                    status="success",
                    duration_ms=duration_ms,
                    result_summary=result_summary,
                    error_message=None,
                    session_id=session_id,
                ))

            return result

        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)

            if access_token:
                asyncio.create_task(self._log_tool_call(
                    access_token=access_token.token,
                    tool_name=tool_name,
                    tool_type=tool_type,
                    arguments=self._truncate_dict(
                        arguments,
                        max_value_len=self.max_value_len
                    ),
                    status="error",
                    duration_ms=duration_ms,
                    result_summary=None,
                    error_message=str(e)[:1000],
                    session_id=session_id,
                ))
            raise

    async def _log_tool_call(
        self,
        access_token: str,
        tool_name: str,
        tool_type: str,
        arguments: dict,
        status: str,
        duration_ms: int,
        result_summary: str | None,
        error_message: str | None,
        session_id: str | None = None,
    ):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    self.log_endpoint,
                    json={
                        "tool_name": tool_name,
                        "tool_type": tool_type,
                        "arguments": arguments,
                        "status": status,
                        "duration_ms": duration_ms,
                        "result_summary": result_summary,
                        "error_message": error_message,
                        "session_id": session_id,
                    },
                    headers={"Authorization": f"Bearer {access_token}"},
                )
        except Exception as e:
            logger.warning(f"Failed to log tool call: {e}")

    async def _get_tool_info(self, access_token: str, tool_name: str) -> AppServerTool | None:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(
                    f"{settings.app_base_url}/api/tool?name={tool_name}",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if response.status_code == 200:
                    return AppServerTool(**response.json())
        except Exception:
            pass
        return None

    def _extract_result_summary(self, result, max_len: int = 500) -> str | None:
        if result is None:
            return None
        
        # Handle ToolResult objects
        if hasattr(result, 'content') and result.content:
            texts = []
            for item in result.content:
                if hasattr(item, 'text'):
                    texts.append(item.text)
                elif hasattr(item, 'data'):
                    texts.append(f"[{item.type}: {len(item.data)} bytes]")
                else:
                    texts.append(str(item))
            summary = "\n".join(texts)
        else:
            summary = str(result)
        
        # If max_len is 0 or less, don't truncate
        if max_len > 0 and len(summary) > max_len:
            return summary[:max_len] + "...[truncated]"
        return summary if summary else None

    def _truncate_dict(self, data: dict, max_value_len: int = 500) -> dict:
        if not data:
            return {}
        truncated = {}
        for k, v in data.items():
            str_v = str(v)
            # If max_value_len is 0 or less, don't truncate
            if max_value_len > 0 and len(str_v) > max_value_len:
                truncated[k] = str_v[:max_value_len] + "...[truncated]"
            else:
                truncated[k] = v
        return truncated


class SessionTrackingMiddleware(Middleware):
    """
    Middleware for tracking active MCP client sessions.
    Maintains in-memory session store for real-time client counting.
    """

    def __init__(self, session_store: SessionStore = None, idle_timeout: int = 300):
        self.sessions = session_store or _session_store
        if idle_timeout != 300 and session_store is None:
            self.sessions._idle_timeout = idle_timeout

    async def on_call_tool(self, context: MiddlewareContext, call_next: CallNext):
        session_id = get_session_id()
        user_id = None
        try:
            token = get_access_token()
            user_id = token.token if token else None
        except Exception:
            pass

        self.sessions.update(session_id, user_id)
        return await call_next(context)

    async def on_list_tools(self, context: MiddlewareContext, call_next: CallNext):
        session_id = get_session_id()
        self.sessions.update(session_id)
        return await call_next(context)

    def get_active_count(self) -> int:
        """Get count of currently active sessions."""
        return self.sessions.get_active_count()

    def get_active_sessions(self) -> Dict[str, Dict]:
        """Get all active session data."""
        return self.sessions.get_active_sessions()


def get_session_store() -> SessionStore:
    """Get the global session store instance."""
    return _session_store
