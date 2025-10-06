# file: app_mcp_dynamic.py
# Python 3.10+
from fastapi import FastAPI, Request, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Callable, Any, Dict, Optional
import asyncio
import inspect
from fastapi.responses import JSONResponse

# Import FastApiMCP from the fastapi_mcp package
# pip install fastapi-mcp
from fastapi_mcp import FastApiMCP

app = FastAPI(title="Dynamic per-user endpoints + FastAPI-MCP demo")

# -----------------------
# Demo auth: token -> user
# -----------------------
TOKENS = {
    "token-alice": "alice",
    "token-bob": "bob",
}

def get_user_from_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    if authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    else:
        token = authorization
    return TOKENS.get(token)

async def current_user(request: Request):
    """Dependency to extract and verify the caller identity.
    FastAPI-MCP can use your existing FastAPI dependencies for auth,
    so keep this as the single place for token validation.
    """
    auth = request.headers.get("Authorization")
    user = get_user_from_token(auth)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token")
    return user

# -----------------------
# In-memory registry & lock
# { owner: { name: callable } }
# -----------------------
CALLABLE_REGISTRY: Dict[str, Dict[str, Callable[..., Any]]] = {}
REGISTRY_LOCK = asyncio.Lock()

class AddCallablePayload(BaseModel):
    name: str
    kind: str = "echo"  # For the demo we support a few preapproved kinds

# -----------------------
# Handler factory (preapproved handlers only)
# -----------------------
def make_handler(kind: str) -> Callable[..., Any]:
    if kind == "echo":
        async def echo_handler(request: Request):
            # simple echo: prefer JSON bodies
            if request.headers.get("content-type", "").startswith("application/json"):
                body = await request.json()
            else:
                body = {"raw": (await request.body()).decode(errors="ignore")}
            return {"kind": "echo", "body": body}
        return echo_handler

    if kind == "hello":
        async def hello_handler(request: Request):
            user = get_user_from_token(request.headers.get("Authorization", ""))
            return {"kind": "hello", "message": f"hello, {user or 'guest'}"}
        return hello_handler

    if kind == "sum":
        async def sum_handler(request: Request):
            payload = await request.json()
            items = payload.get("items", [])
            try:
                s = sum(float(x) for x in items)
            except Exception:
                raise HTTPException(status_code=400, detail="items must be numeric list")
            return {"kind": "sum", "sum": s}
        return sum_handler

    async def default_handler(request: Request):
        return {"kind": "default", "msg": "no-op"}
    return default_handler

# -----------------------
# Admin endpoints (protected by current_user)
# These let an authenticated user register their own callable.
# -----------------------
@app.post("/admin/callables", response_model=dict)
async def admin_add_callable(payload: AddCallablePayload, user: str = Depends(current_user)):
    async with REGISTRY_LOCK:
        owner_map = CALLABLE_REGISTRY.setdefault(user, {})
        if payload.name in owner_map:
            raise HTTPException(status_code=400, detail="callable name already exists for this user")
        handler = make_handler(payload.kind)
        owner_map[payload.name] = handler
    return {"status": "added", "owner": user, "name": payload.name, "kind": payload.kind}

@app.delete("/admin/callables/{name}", response_model=dict)
async def admin_remove_callable(name: str, user: str = Depends(current_user)):
    async with REGISTRY_LOCK:
        owner_map = CALLABLE_REGISTRY.get(user, {})
        if name not in owner_map:
            raise HTTPException(status_code=404, detail="callable not found")
        del owner_map[name]
    return {"status": "removed", "owner": user, "name": name}

@app.get("/admin/callables", response_model=dict)
async def admin_list_callables(user: str = Depends(current_user)):
    owner_map = CALLABLE_REGISTRY.get(user, {})
    return {"owner": user, "callables": list(owner_map.keys())}

# -----------------------
# Generic dispatcher route
# - This is the single HTTP path that actually runs user-registered callables
# - It enforces ownership: only the owner (token) can call their callable
# - This route will be converted into an MCP tool by fastapi_mcp when mounted
# -----------------------
@app.api_route("/dyn/{name}", methods=["GET", "POST", "PUT", "DELETE"], include_in_schema=True)
async def dynamic_dispatch(name: str, request: Request, caller: str = Depends(current_user)):
    # Enforce the owner: user must own the callable named `name`
    owner_map = CALLABLE_REGISTRY.get(caller, {})
    handler = owner_map.get(name)
    if not handler:
        # Return 404 to avoid leaking existence of other users' callables
        raise HTTPException(status_code=404, detail="callable not found")

    # Support sync or async handlers
    if inspect.iscoroutinefunction(handler):
        return await handler(request)
    else:
        from fastapi.concurrency import run_in_threadpool
        return await run_in_threadpool(handler, request)

# -----------------------
# Simple utility endpoint for testing auth
# -----------------------
@app.get("/whoami")
async def whoami(user: str = Depends(current_user)):
    return {"user": user}

@app.get("/")
async def root():
    return {"msg": "Dynamic endpoints + FastAPI-MCP demo. MCP mounted at /mcp"}

# -----------------------
# Mount FastAPI-MCP (expose your FastAPI app as MCP tools)
#
# Basic usage (quickstart): create the FastApiMCP wrapper and mount it.
# This uses your existing FastAPI app and its dependencies (so your
# current_user dependency will be used by the MCP server for auth).
#
# See fastapi-mcp quickstart / README for details.  [oai_citation:1‡GitHub](https://github.com/tadata-org/fastapi_mcp)
# -----------------------
mcp = FastApiMCP(app)

# You can choose mount_http() or mount() depending on the version/options;
# quickstart shows mcp.mount() or mcp.mount_http() — pick the one available
# in your installed fastapi-mcp. We'll call mount_http() (works on recent versions).

mcp.mount_http()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8090)
