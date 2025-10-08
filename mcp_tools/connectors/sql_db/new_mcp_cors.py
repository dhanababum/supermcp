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
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
import requests
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.types import Receive, Scope, Send
from pydantic import BaseModel
import jwt
from typing import Any, Callable, Dict, List
from fastapi import Request
from utils import CustomFastMCP as FastMCP, Template
from fastmcp.server.dependencies import get_access_token
from fastmcp.tools import Tool
from fastmcp.tools.tool_transform import ArgTransform, TransformedTool
from starlette.middleware.base import BaseHTTPMiddleware

from fastmcp.server.middleware.middleware import (
    Middleware, MiddlewareContext, CallNext
)
from starlette.responses import FileResponse, JSONResponse
from mcp.types import TextContent, Tool as MCPTool

from fastmcp.server.auth import RemoteAuthProvider

from fastmcp.server.auth.providers.jwt import JWTVerifier, RSAKeyPair, TokenVerifier, AccessToken
from schema import SqlDbSchema
# Generate a key pair for testing
key_pair = RSAKeyPair.generate()


class Table(BaseModel):
    name: str
    description: str
    columns: List[str]


class CustomTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        print("Verifying token................")
        req = requests.get(
            "http://127.0.0.1:9000/api/verify-auth-token",
            headers={"Authorization": f"Bearer {token}"}
        )
        # token = "dummy"
        if req.status_code != 200:
            return None
        return AccessToken(
            token=token,
            client_id="dummy",
            scopes=["read", "write", "admin"]
        )


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


verifier = CustomTokenVerifier(
    base_url="http://127.0.0.1:9000",
)


# ---------- Create MCP server
mcp = FastMCP(
    "owner-demo",
    # stateless_http=True,
    auth=verifier,
)

# @mcp.custom_route("/hello", methods=["GET"])
# def hello(request: Request) -> str:
#     return PlainTextResponse(f"Hello, {request}")


@mcp.tool(enabled=True)
def hello_tool_x(name: str, age: int) -> str:
    """
    Hello tool
    """
    return f"Hello, {name}!"


@mcp.template("hello")
def hello_template(name: str, age: int):
    """
    Hello template
    """
    async def dynamic_hello(**kwargs):
        print(f"Dat: {dynamic_hello.__annotations__}")
        return name.format(**kwargs)
    return dynamic_hello


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

    async def on_call_tool(self, context: MiddlewareContext, call_next: CallNext):
        print(f"On call tool................", context)
        access_token = get_access_token()

        # tool = await context.fastmcp_context.fastmcp.get_tool(tool_name)
        server_tool = await self.get_tool_by_name(access_token.token, context.message.name)
        
        if server_tool and server_tool["tool_type"] == "dynamic":
            template = mcp.get_template(server_tool["tool"]["template_name"])
            dynamic_function = template.template_function(**server_tool["tool"]["template_args"])
            # import pdb; pdb.set_trace()
            result = ToolResult(
                content=[TextContent(type="text", text=await dynamic_function(**context.message.arguments))],
            )
            return result
        elif not server_tool:
            raise ToolError(f"Access denied to private tool: {context.message.name}")
        print(f"Context: {context}")
        print(f"Access token: {access_token}")
        tool = await call_next(context)
        return tool

    async def on_list_tools(self, context: MiddlewareContext, call_next: CallNext):
        # Get the full list of Tool objects from the inner server
        # import pdb; pdb.set_trace()
          # list[Tool]
        access_token = get_access_token()
        print(f"Context: {context}")
        print(f"Access token: {access_token}")
        # print(f"Tools: {tools}")
        # req = requests.get("http://127.0.0.1:9000/api/")
        online_tools = await self.get_active_tools(access_token.token)
        print(f"Online tools: {online_tools}")
        static_tools = [tool["tool"]["name"] for tool in online_tools if tool["tool_type"] == "static"]
        tools = await call_next(context)
        new_tools = []
        for tool in tools:
            if tool.name in set(static_tools):
                new_tools.append(tool)
        for server_tool in online_tools:
            tool = server_tool["tool"]
            if server_tool["tool_type"] == "dynamic":
                template_name = server_tool["template_name"]
                template: Template = mcp.get_template(template_name)
                
                new_tool = Tool(
                    name=tool["name"],
                    parameters=tool.get("inputSchema", {}),
                    description=tool.get("description", ""),
                    annotations=tool.get("annotations", {}),
                    meta=tool.get("meta", {}),
                )
                
                t_tool = TransformedTool.from_tool(
                    new_tool,
                    transform_fn=template.template_function(
                        **server_tool["template_args"]),
                    annotations=tool.get("annotations", {}),
                    meta=tool.get("meta", {}),
                )
                # tool = context.fastmcp_context.fastmcp.add_tool(t_tool)
                # context.fastmcp_context.fastmcp.add_tool(t_tool)
                print(f"Tool: {tool}")
                new_tools.append(t_tool)
        
                # import pdb; pdb.set_trace()
        # print(f"Tools: {tools}")
        # tools = [tool for tool in tools if tool.name in online_tools]
        return new_tools
    
    async def get_active_tools(self, access_token: str):
        req = requests.get("http://127.0.0.1:9000/api/tools", headers={"Authorization": f"Bearer {access_token}"})
        return req.json()

    async def get_tool_by_name(self, access_token: str, tool_name: str):
        req = requests.get(f"http://127.0.0.1:9000/api/tool?name={tool_name}", headers={"Authorization": f"Bearer {access_token}"})
        return req.json() if req.status_code == 200 else None


# Test getting tools (await the coroutine)
mcp.add_middleware(OwnerFilterMiddleware())
print("Listing middleware................")
print(mcp.middleware)
app = mcp.http_app()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Replace with your client's origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods, including those in Access-Control-Request-Method
    allow_headers=["*"],  # Allow all headers
    expose_headers=["mcp-session-id"]
)
# mcp.add_middleware(OwnerFilterMiddleware())
# ---------- Run server (HTTP transport so Postman / curl can talk JSON-RPC)
if __name__ == "__main__":
    # Run an HTTP streamable MCP endpoint at http://127.0.0.1:8000/mcp
    print("Starting MCP server at http://127.0.0.1:8000/mcp")
    # Use HTTP transport (streamable HTTP). Adjust host/port/path as needed.
    # mcp.run(transport="http", host="127.0.0.1", port=8015, path="/mcp")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8016)
