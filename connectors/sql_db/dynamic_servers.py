from fastapi import FastAPI, APIRouter, Depends, HTTPException, Header, Query, status
from fastmcp import FastMCP
from fastmcp.server.auth import TokenVerifier, AccessToken
from starlette.applications import Starlette
from middleware import AuthMiddleware
from constants import tokens, mcp_servers

# mcp = DynamicFastMCP(
#     streamable_http_path="/",
# )


def verify_token(authorization: str = Header(...)):
    # In a real app, you would decode the JWT and check its validity.
    # For this example, we use a simple hardcoded token.
    if authorization != "Bearer my-secret-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return authorization


class CustomTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        # Implement your token verification logic
        if token in tokens:
            return AccessToken(token=token, client_id="client_123", scopes=[])
        return None


mcp = FastMCP(
    "dynamic-servers",
    # auth=CustomTokenVerifier(),
    # verify_token=verify_token,
)


@mcp.tool()
def hello_tool(name: str, age: int) -> str:
    """
    A simple hello tool that greets a person.
    """
    return f"Hello, {name}! You are {age} years old."


mcp_app = mcp.http_app()
app = Starlette(lifespan=mcp_app.lifespan)
# mcp_app.add_middleware(AuthMiddleware)
# app.add_middleware(AuthMiddleware)
# Mount MCP at different paths for multi-tenant support


@app.post("/create-server/{server_id}")
def create_new_mcp_server(server_id: str):
    """Endpoint to dynamically create and mount a new server."""
    if server_id in mcp_servers:
        return {"message": f"Server {server_id} already exists."}

    app.mount(f"/mcp/{server_id}", app=mcp_app, name=server_id)
    mcp_servers.add(server_id)
    return {
        "message": f"Server {server_id} created and mounted at /mcp/{server_id}"}


@app.get("/servers")
def get_servers():
    return {"servers": list(mcp_servers)}


@app.post("/create-token")
def create_token(
    token: str = Query(...),
):
    tokens[token] = "client_123"
    return {"message": "Token created"}


@app.get("/remove-token")
def remove_token(
    token: str = Query(...),
):
    if token not in tokens:
        return {"message": "Token not found"}
    tokens.pop(token)
    return {"message": "Token removed"}

app.mount("/mcp-noauth/shared", app=mcp_app)


# Create MCP instance with authentication
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8020)
