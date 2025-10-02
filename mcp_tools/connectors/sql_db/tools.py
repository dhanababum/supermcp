"""
This example shows how to reject any request without a valid token passed in the Authorization header.

In order to configure the auth header, the config file for the MCP server should looks like this:
```json
{
  "mcpServers": {
    "remote-example": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://localhost:8000/mcp",
        "--header",
        "Authorization:${AUTH_HEADER}"
      ]
    },
    "env": {
      "AUTH_HEADER": "Bearer <your-token>"
    }
  }
}
```
"""


from fastapi import Depends, FastAPI
from fastapi.security import HTTPBearer

from fastapi_mcp import FastApiMCP, AuthConfig
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, engine as sqlalchemy_engine
from sqlalchemy.orm import sessionmaker
from contextvars import ContextVar
import asyncio
app = FastAPI()

# Scheme for the Authorization header
token_auth_scheme = HTTPBearer()


# Create a private endpoint
@app.get("/private")
async def private(token=Depends(token_auth_scheme)):
    return token.credentials
databases = {}


@app.get("/database-connect")
def connect_to_database(token=Depends(token_auth_scheme), db_path: str = 'test.db') -> dict:
    """
    Connects to a SQLite database file and sets up the session factory.

    Args:
        db_path: The file path to the SQLite database.
    """
    try:
        # Create a new engine for the specific database path
        databases[token.credentials] = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        # Set the engine in the context variable for subsequent calls
        return {"success": True, "message": f"Successfully connected to {db_path}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.get("/get-records")
async def get_records(token=Depends(token_auth_scheme), table_name: str = 'albums', limit: int = 10) -> list | dict:
    """
    Retrieves records from a specified table using the current database connection.

    Args:
        table_name: The name of the table to query.
        limit: The maximum number of records to return.
    """
    
    # import pdb; pdb.set_trace()
    engine = databases.get(token.credentials, None)
    if not engine:
        return {"error": "No database connected. Call 'connect_to_database' first."}

    # Create an async session and execute the query

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            from sqlalchemy import text
            result = await session.execute(text(f"SELECT * FROM {table_name} LIMIT :limit"), {"limit": limit})
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e)}


# Create the MCP server with the token auth scheme
mcp = FastApiMCP(
    app,
    name="Protected MCP",
    auth_config=AuthConfig(
        dependencies=[Depends(token_auth_scheme)],
    ),
)

# Mount the MCP server
mcp.mount_http()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010)
