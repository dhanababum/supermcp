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

import requests
import time
import json
from fastapi import Depends, FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, _StreamingResponse as StreamingResponse
# from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer

from fastapi_mcp import FastApiMCP, AuthConfig
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, engine as sqlalchemy_engine
from sqlalchemy.orm import sessionmaker
from contextvars import ContextVar
import asyncio
from config import SqlDbConfig

config = SqlDbConfig()

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
        response = requests.get(f"{config.API_URL}/server-config/{token.credentials}")
        if response.status_code != 200:
            return {"success": False, "message": "Failed to get connector configuration"}
        connector_config = response.json()
        database_url = connector_config.get("configuration", {}).get("database_url")
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


def create_endpoint(m_name: str):
    async def endpoint(request: Request):
        print(request.url)
        return f"You called {m_name}"
    return endpoint

def dynamic_endpoint(m_name: str):
    return {
            "name": f"{m_name}_database_connect_get",
            "description": f"query to {m_name}",
            "inputSchema":
              {
                "type": "object",
                "properties":
                  {
                    "db_path":
                      {
                        "type": "string",
                        "default": "test.db",
                        "title": "db_path",
                      },
                  },
                "title": f"{m_name}_database_connect_getArguments",
              },
          }


class StreamingInterceptorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        

        # create a new Request bound to the same scope but new receive
        # new_request = Request(request.scope, receive)
        try:
            # Get the response from the next middleware or the endpoint
            response = await call_next(request)
        except Exception as e:
            # Handle potential exceptions during the call
            return Response(f"Internal Server Error: {e}", status_code=500)
        
        # Check if the response is a StreamingResponse
        if isinstance(response, StreamingResponse):

            # Create a new generator function that wraps the original
            async def intercept_stream_generator():
                async for chunk in response.body_iterator:
                    # Your interception logic here
                    # remove specific tools from the response
                    if "result" in chunk.decode('utf-8'):
                        
                        response_json = json.loads(chunk.decode('utf-8'))
                        if "result" in response_json and "tools" in response_json["result"]:
                            # get token from request
                            # message = await request.receive()
                            # print(f"Message: {message}")
                            # app.add_api_route(f"/{m.__name__.lower()}", create_endpoint(m.__name__), methods=["GET"])

                            token = request.headers.get('Authorization')
                            tool = dynamic_endpoint("sample_function")
                            response_json["result"]["tools"].append(tool)
                            chunk = json.dumps(response_json).encode('utf-8')
                    # print(f"Intercepted chunk: {chunk.decode('utf-8')}")
                    yield chunk
            
            # Create new headers without Content-Length since we're modifying the content
            # This allows chunked transfer encoding to be used instead
            new_headers = dict(response.headers)
            new_headers.pop('content-length', None)
            new_headers.pop('Content-Length', None)
            
            # Return a new StreamingResponse with the wrapped generator
            return StreamingResponse(
                content=intercept_stream_generator(),
                status_code=response.status_code,
                headers=new_headers,
                media_type=response.media_type
            )
        
        return response

# Add the middleware to the application
app.add_middleware(StreamingInterceptorMiddleware)

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
