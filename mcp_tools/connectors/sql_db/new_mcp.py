# mcp_owner_demo.py
"""
Run with:
    python mcp_owner_demo.py

Then point an MCP client or send raw MCP JSON-RPC POSTs to:
    http://127.0.0.1:8000/mcp

This example registers a few demo tools owned by 'alice' and 'bob'.
Use Authorization: "Bearer token-alice" or "Bearer token-bob" when listing/calling.

Notes:
- Uses FastMCP from the MCP Python SDK (fastmcp wrapper).
- No FastAPI / no fastapi_mcp used.
"""
import pdb
import os
from starlette.types import Receive, Scope, Send
from pydantic import BaseModel
import jwt
from typing import Any, Callable, Dict, List
from fastapi import Request
from utils import CustomFastMCP as FastMCP
from fastmcp.server.dependencies import get_access_token
from fastmcp.tools import Tool
from fastmcp.tools.tool_transform import ArgTransform
from starlette.middleware.base import BaseHTTPMiddleware

from fastmcp.server.middleware.middleware import (
    Middleware, MiddlewareContext, CallNext
)
from starlette.responses import FileResponse, JSONResponse
from mcp.types import Tool as MCPTool


from fastmcp.server.auth.providers.jwt import JWTVerifier, RSAKeyPair
from schema import SqlDbSchema
# Generate a key pair for testing
key_pair = RSAKeyPair.generate()


class Table(BaseModel):
    name: str
    description: str
    columns: List[str]


# Configure your server with the public key
verifier = JWTVerifier(
    public_key=key_pair.public_key,
    issuer="https://test.yourcompany.com",
    audience="test-mcp-server"
)

# Generate a test token using the private key
test_token = key_pair.create_token(
    subject="test-user-123",
    issuer="https://test.yourcompany.com", 
    audience="test-mcp-server",
    scopes=["read", "write", "admin"]
)

print(f"Test token: {test_token}")

# ---------- Demo token -> user mapping (replace with real auth/jwt in prod)
TOKENS = {
    "token-alice": "alice",
    "token-bob": "bob",
}

def user_from_auth_header(auth: str | None) -> str | None:
    if not auth:
        return None
    if auth.startswith("Bearer "):
        tok = auth.split(" ", 1)[1]
    else:
        tok = auth
    return TOKENS.get(tok)


# ---------- Create MCP server
mcp = FastMCP(
    "owner-demo",
    # auth=verifier,
)



# @mcp.custom_route("/hello", methods=["GET"])
# def hello(request: Request) -> str:
#     return PlainTextResponse(f"Hello, {request}")


@mcp.tool(enabled=True)
def hello_tool_x(name: str, age: int) -> Table:
    """
    Hello tool
    """
    return f"Hello, {name}!"

new_tool = Tool.from_tool(
    hello_tool_x,
    transform_args={
        "name": ArgTransform(name="search_query")
    },
#     output_schema={
#         "type": "object",
#         "properties": {"status": {"type": "string"}}
# }
)


mcp.add_tool(new_tool)

@mcp.template("hello")
def hello_template(name: str, age: int) -> str:
    """
    Hello template
    """
    return f"Hello, {name}!"


# hello_tool_x.disable()
# ---------- Helper: register a demo tool for an owner
# We'll name each tool: "<owner>__<short_name>" so middleware can filter on owner prefix.
def register_owner_tool(owner: str, short_name: str,
                       fn: Callable[..., Any],
                       description: str | None = None):
    tool_name = f"{owner}__{short_name}"
    # FastMCP's add_tool / tool decorator will register the callable as a tool.
    # Prefer using mcp.add_tool if available; else fall back to decorator.
    wrapped = fn
    # use mcp.tool to register (this will register by function __name__ normally; to be safe we set __name__)
    wrapped.__name__ = tool_name
    mcp.tool(wrapped)

# ---------- Demo tool implementations (simple)
def make_echo_tool(owner: str, short_name: str):
    async def echo(payload: dict) -> dict:
        # just return the payload and the owner info
        return {"owner": owner, "name": short_name, "payload": payload}
    return echo

def make_info_tool(owner: str, short_name: str):
    def info() -> dict:
        return {"owner": owner, "name": short_name, "msg": f"static info from {owner}/{short_name}"}
    return info

# Register some demo tools for the JWT test user

@mcp.custom_route("/logo.png", methods=["GET"])
async def get_logo(request: Request):
    return FileResponse(os.path.join(os.path.dirname(__file__), "media/sqldb.png"))


@mcp.custom_route("/connector.json", methods=["GET"])
async def get_tools(request: Request):
    host = request.headers.get("host")
    server_config = {
        **SqlDbSchema.model_json_schema(),
    }
    tools = await mcp.get_tools()
    templates = mcp.get_templates()
    tools_list = []
    for name, tool in tools.items():
        tool: MCPTool = tool.to_mcp_tool()
        tools_list.append({
            "name": name,
            "title": tool.title,
            "icons": tool.icons,
            "description": tool.description,
            "inputSchema": tool.inputSchema,
            "outputSchema": tool.outputSchema,
            "annotations": tool.annotations,
            "meta": tool.meta,
        })
    templates_list = []
    for name, template in templates.items():
        templates_list.append({
            "name": name,
            "description": template.description,
            **template.params,
        })
    data = {
        "version": "1.0.0",
        "description": "SQL DB MCP",
        "name": "sql_db_mcp",
        "url": f"http://{host}/connector.json",
        "config": server_config,
        "tools": tools_list,
        "templates": templates_list,
        "logo_url": f"http://{host}/logo.png",
    }
    return JSONResponse(data)

# In your FastMCP server setup:
# server.add_middleware(AuthMiddleware(MyTokenVerifier()))
# ---------- Middleware: filter listTools by token -> user, and enforce on callTool
class OwnerFilterMiddleware(Middleware):
    """
    - on_list_tools: call_next returns the full tool list, we filter to include only tools
      whose names are prefixed by '<user>__'.
    - on_call_tool: ensure the requested tool name belongs to the caller (owner prefix match).
    """

    async def on_list_tools(self, context: MiddlewareContext, call_next: CallNext):
        # Get the full list of Tool objects from the inner server
        tools = await call_next(context)  # list[Tool]
        access_token = get_access_token()
        print(f"Access token: {access_token}")
        print(f"Tools: {tools}")
        return tools

# Test getting tools (await the coroutine)
# mcp.add_middleware(OwnerFilterMiddleware())

# ---------- Run server (HTTP transport so Postman / curl can talk JSON-RPC)
if __name__ == "__main__":
    # Run an HTTP streamable MCP endpoint at http://127.0.0.1:8000/mcp
    print("Starting MCP server at http://127.0.0.1:8000/mcp")
    # Use HTTP transport (streamable HTTP). Adjust host/port/path as needed.
    mcp.run(transport="http", host="127.0.0.1", port=8015, path="/mcp")
