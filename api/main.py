import sys
import secrets
from pathlib import Path
from datetime import datetime
from typing import List
import requests

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi_mcp.openapi.convert import convert_openapi_to_mcp_tools
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from mcp_tools.connectors import get_all_connectors, get_connector_schema
from api.models import McpServer, McpServerToken, McpServerTool
from api.database import get_session

app = FastAPI(title="MCP Tools API", description="API for MCP Tools", version="0.1.0")

# Create database tables on startup
# NOTE: Table creation is now handled by Alembic migrations
# Run: uv run alembic upgrade head
@app.on_event("startup")
def on_startup():
    # create_db_and_tables()  # Disabled - use Alembic migrations
    pass

# Add CORS middleware to allow requests from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(
    prefix="/api",
)


@router.get("/")
def read_root():
    return {"message": "Hello, World!"}


@router.get("/connectors")
def get_connectors() -> list:
    return get_all_connectors()


@router.get("/connector-schema/{connector_name}")
def get_connector_schema_endpoint(connector_name: str) -> dict:
    return get_connector_schema(connector_name)


@router.post("/servers")
def create_server(
    server_data: dict,
    session: Session = Depends(get_session)
) -> dict:
    # Ensure connector_name and server_name are provided
    if "connector_name" not in server_data:
        raise HTTPException(status_code=400, detail="connector_name is required")
    if "server_name" not in server_data:
        raise HTTPException(status_code=400, detail="server_name is required")
    
    # Extract token_expires_at if provided
    token_expires_at = server_data.pop("token_expires_at", None)
    
    # Parse the expiry date if it's a string
    if token_expires_at:
        if isinstance(token_expires_at, str):
            try:
                from dateutil import parser
                token_expires_at = parser.parse(token_expires_at)
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid token_expires_at format"
                )
    
    mcp_server = McpServer(**server_data)
    session.add(mcp_server)
    session.commit()
    session.refresh(mcp_server)

    connector_urls = {
        "sql_db": "http://localhost:8010/openapi.json"
    }
    openapi_url = connector_urls.get(mcp_server.connector_name)
    
    openapi_data = requests.get(openapi_url).json()
    tools, _ = convert_openapi_to_mcp_tools(openapi_data)
    # Generate a secure tool
    for mcp_tool in tools:
        db_tool = McpServerTool(
            tool_name=mcp_tool.name,
            tool_title=mcp_tool.title if hasattr(mcp_tool, 'title') and mcp_tool.title else mcp_tool.name,
            tool_description=mcp_tool.description,
            tool_input_schema=mcp_tool.input_schema if hasattr(mcp_tool, 'input_schema') else (mcp_tool.inputSchema if hasattr(mcp_tool, 'inputSchema') else {}),
            tool_output_schema={},
            mcp_server_id=mcp_server.id
        )

        session.add(db_tool)
        session.commit()
        session.refresh(db_tool)
    # Generate a secure token
    token_value = f"mcp_token_{secrets.token_urlsafe(32)}"
    token = McpServerToken(
        token=token_value,
        mcp_server_id=mcp_server.id,
        expires_at=token_expires_at
    )
    session.add(token)
    session.commit()
    session.refresh(token)


    return {
        "status": "created",
        "message": f"Server '{mcp_server.server_name}' created successfully",
        "server_id": mcp_server.id,
        "connector_name": mcp_server.connector_name,
        "server_name": mcp_server.server_name,
        "token": token_value,
        "token_expires_at": token.expires_at.isoformat() if token.expires_at else None
    }


@router.get("/servers")
def list_all_servers(
    session: Session = Depends(get_session)
) -> List[dict]:
    """
    List all active server configurations.
    """
    statement = select(McpServer).where(
        McpServer.is_active.is_(True)
    ).order_by(McpServer.updated_at.desc())
    
    configs = session.exec(statement).all()
    
    return [
        {
            "id": config.id,
            "connector_name": config.connector_name,
            "server_name": config.server_name,
            "configuration": config.configuration,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
            "is_active": config.is_active
        }
        for config in configs
    ]


@router.get("/servers/{server_id}")
def get_server(
    server_id: int,
    session: Session = Depends(get_session)
) -> dict:
    """
    Retrieve the active configuration for a specific server.
    """
    statement = select(McpServer).where(
        McpServer.id == server_id,
        McpServer.is_active.is_(True)
    )
    config = session.exec(statement).first()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"No server found with id: {server_id}")
    
    return {
        "id": config.id,
        "connector_name": config.connector_name,
        "server_name": config.server_name,
        "configuration": config.configuration,
        "created_at": config.created_at.isoformat(),
        "updated_at": config.updated_at.isoformat(),
        "is_active": config.is_active
    }


@router.put("/servers/{server_id}")
def update_server(
    server_id: int,
    config_data: dict,
    session: Session = Depends(get_session)
) -> dict:
    """
    Save or update a server configuration.
    Uses JSONB to store dynamic schema data.
    """
    try:
        # Check if configuration already exists for this server
        statement = select(McpServer).where(
            McpServer.id == server_id,
            McpServer.is_active.is_(True)
        )
        existing_config = session.exec(statement).first()
        
        if not existing_config:
            raise HTTPException(status_code=404, detail=f"No server found with id: {server_id}")
        
        # Update existing configuration
        existing_config.configuration = config_data
        existing_config.updated_at = datetime.utcnow()
        session.add(existing_config)
        session.commit()
        session.refresh(existing_config)
        
        return {
            "status": "updated",
            "message": f"Configuration for server '{existing_config.server_name}' updated successfully",
            "server_id": existing_config.id,
            "connector_name": existing_config.connector_name,
            "server_name": existing_config.server_name
        }

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update server: {str(e)}")


@router.delete("/servers/{server_id}")
def delete_server(
    server_id: int,
    session: Session = Depends(get_session)
) -> dict:
    """
    Soft delete a server configuration and all related data (marks as inactive).
    This includes the server, all its tokens, and all its tools.
    """
    try:
        # Get the server
        statement = select(McpServer).where(
            McpServer.id == server_id,
            McpServer.is_active.is_(True)
        )
        server = session.exec(statement).first()
        
        if not server:
            raise HTTPException(status_code=404, detail=f"No server found with id: {server_id}")
        
        # Mark all related tokens as inactive
        token_statement = select(McpServerToken).where(
            McpServerToken.mcp_server_id == server_id,
            McpServerToken.is_active.is_(True)
        )
        tokens = session.exec(token_statement).all()
        tokens_count = len(tokens)
        
        for token in tokens:
            token.is_active = False
            token.updated_at = datetime.utcnow()
            session.add(token)
        
        # Mark all related tools as inactive
        tool_statement = select(McpServerTool).where(
            McpServerTool.mcp_server_id == server_id,
            McpServerTool.is_active.is_(True)
        )
        tools = session.exec(tool_statement).all()
        tools_count = len(tools)
        
        for tool in tools:
            tool.is_active = False
            tool.updated_at = datetime.utcnow()
            session.add(tool)
        
        # Mark server as inactive
        server.is_active = False
        server.updated_at = datetime.utcnow()
        session.add(server)
        
        # Commit all changes
        session.commit()
        
        return {
            "status": "deleted",
            "message": f"Server '{server.server_name}' and all related data deleted successfully",
            "server_id": server_id,
            "deleted_tokens": tokens_count,
            "deleted_tools": tools_count
        }
    
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete server: {str(e)}")


@router.get("/servers/{server_id}/tools")
def get_server_tools(
    server_id: int,
    session: Session = Depends(get_session)
) -> dict:
    """
    Retrieve the available tools from a specific MCP server.
    Makes a request to the MCP server endpoint using the server's token.
    """
    
    # Get the server configuration
    statement = select(McpServer).where(
        McpServer.id == server_id,
        McpServer.is_active.is_(True)
    )
    server = session.exec(statement).first()
    
    if not server:
        raise HTTPException(status_code=404, detail=f"No server found with id: {server_id}")
    
    # Get an active token for this server
    token_statement = select(McpServerToken).where(
        McpServerToken.mcp_server_id == server_id,
        McpServerToken.is_active.is_(True)
    )
    token = session.exec(token_statement).first()
    
    if not token:
        raise HTTPException(status_code=404, detail=f"No active token found for server id: {server_id}")
    
    # Check if token is expired
    if token.expires_at and token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Token has expired")
    
    # Get tools from database
    tool_statement = select(McpServerTool).where(
        McpServerTool.mcp_server_id == server_id,
        McpServerTool.is_active.is_(True)
    )
    db_tools = session.exec(tool_statement).all()
    
    # Transform database tools to MCP format
    tools = []
    for tool in db_tools:
        tools.append({
            "name": tool.tool_name,
            "description": tool.tool_description,
            "inputSchema": tool.tool_input_schema if tool.tool_input_schema else {}
        })

    return {
        "server_id": server.id,
        "server_name": server.server_name,
        "connector_name": server.connector_name,
        "tools": tools
    }
    

app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
