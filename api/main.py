from ast import Dict
import sys
import secrets
import logging
import uuid
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List
import requests

from datatypes import McpServerToolItem, ToolType, McpConnectorTemplateItem
from datatypes import UserCreate, UserRead, UserUpdate
from users import jwt_auth_backend, cookie_auth_backend, current_active_user, fastapi_users

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Disable SQLAlchemy logging to reduce verbosity
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm').setLevel(logging.WARNING)

from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from pydantic import BaseModel
from models import McpConnector, McpServer, McpServerToken, McpServerTool, User, ConnectorAccess
from database import get_session
from utils import store_logo, get_tool_id
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


app = FastAPI(title="MCP Tools API", description="API for MCP Tools", version="0.1.0")


class CreateConnectorRequest(BaseModel):
    connector_url: str


class CreateToolFromTemplateRequest(BaseModel):
    connector_id: int
    template_name: str
    template_params: dict
    tool_name: str
    description: str


class AuthRequest(BaseModel):
    token: str


class GrantConnectorAccessRequest(BaseModel):
    user_id: uuid.UUID
    connector_id: int


class RevokeConnectorAccessRequest(BaseModel):
    user_id: uuid.UUID
    connector_id: int


class UpdateUserRoleRequest(BaseModel):
    is_superuser: bool


token_header = HTTPBearer()


# create auth dependency & verify with McpServerToken
def get_auth_token(
    token: HTTPAuthorizationCredentials = Depends(token_header),
    session: Session = Depends(get_session)
):
    print(f"Verifying token: {token.credentials}")
    token_statement = select(McpServerToken).where(
        McpServerToken.token == token.credentials,
        McpServerToken.is_active.is_(True)
    )
    server_token = session.exec(token_statement).first()
    print(f"Token: {type(server_token)}")
    if not server_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    print("..........")
    return server_token


def get_all_connectors(session: Session):
    connectors = session.exec(
                    select(McpConnector)
                ).all()
    return connectors


def is_superuser(user: User) -> bool:
    """Check if user has superuser role using fastapi-users built-in field."""
    return user.is_superuser


def check_superuser_access(user: User):
    """Raise HTTPException if user is not a superuser."""
    if not is_superuser(user):
        raise HTTPException(
            status_code=403, 
            detail="Access denied. Superuser role required."
        )


def require_superuser():
    """FastAPI dependency that requires superuser access."""
    def superuser_dependency(user: User = Depends(current_active_user)):
        check_superuser_access(user)
        return user
    return superuser_dependency


def get_user_accessible_connectors(session: Session, user: User) -> List[McpConnector]:
    """Get connectors that the user has access to."""
    if is_superuser(user):
        # Superusers can see all connectors
        return session.exec(select(McpConnector).where(McpConnector.is_active.is_(True))).all()
    else:
        # Regular users can only see connectors they have access to
        statement = select(McpConnector).join(ConnectorAccess).where(
            ConnectorAccess.user_id == user.id,
            ConnectorAccess.is_active.is_(True),
            McpConnector.is_active.is_(True)
        )
        return session.exec(statement).all()


def check_connector_access(session: Session, user: User, connector_id: int) -> McpConnector:
    """Check if user has access to a specific connector and return it."""
    if is_superuser(user):
        # Superusers can access any connector
        connector = session.get(McpConnector, connector_id)
        if not connector or not connector.is_active:
            raise HTTPException(status_code=404, detail="Connector not found")
        return connector
    else:
        # Regular users need explicit access
        statement = select(McpConnector).join(ConnectorAccess).where(
            McpConnector.id == connector_id,
            ConnectorAccess.user_id == user.id,
            ConnectorAccess.is_active.is_(True),
            McpConnector.is_active.is_(True)
        )
        connector = session.exec(statement).first()
        if not connector:
            raise HTTPException(
                status_code=403, 
                detail="Access denied. You don't have access to this connector."
            )
        return connector


def create_connector_record(connector_data: dict, session: Session, user_id: uuid.UUID = None):
    if user_id:
        connector_data["created_by"] = user_id
    connector = McpConnector(**connector_data)
    session.add(connector)
    session.commit()
    session.refresh(connector)
    return connector


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

root_router = APIRouter()

router = APIRouter(
    prefix="/api",
)

app.include_router(
    fastapi_users.get_auth_router(jwt_auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_auth_router(cookie_auth_backend), prefix="/auth/cookie", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}


@router.get("/")
def read_root():
    return {"message": "Hello, World!"}


@router.get("/connectors")
def get_connectors(
    session: Session = Depends(get_session),
    current_user: User = Depends(current_active_user)
) -> list:
    print(f"Current user: {current_user}")
    print(f"Current user ID: {current_user.id}")
    print(f"Current user is_superuser: {current_user.is_superuser}")
    
    try:
        # Get connectors based on user role and access
        connectors = get_user_accessible_connectors(session, current_user)
        print(f"Found {len(connectors)} accessible connectors")
        
        # Convert to dict to avoid relationship serialization issues
        result = []
        for connector in connectors:
            result.append({
                "id": connector.id,
                "name": connector.name,
                "url": connector.url,
                "description": connector.description,
                "version": connector.version,
                "logo_url": connector.logo_url,
                "created_at": connector.created_at.isoformat() if connector.created_at else None,
                "updated_at": connector.updated_at.isoformat() if connector.updated_at else None,
                "is_active": connector.is_active
            })
        
        return result
    except Exception as e:
        print(f"Error in get_connectors: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/connectors")
def create_connector(
    request: CreateConnectorRequest, 
    session: Session = Depends(get_session),
    current_user: User = Depends(require_superuser())
) -> dict:
    req = requests.get(request.connector_url)
    if req.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get connector schema")
    connector_data = req.json()
    
    # Extract required fields with defaults
    name = connector_data.get("name", "Unknown Connector")
    tools = connector_data.get("tools", [])
    templates = connector_data.get("templates", {})
    server_config = connector_data.get("config", {})
    
    # Convert tools to McpConnectorToolItem objects
    # from datatypes import McpConnectorToolItem
    # tools_config = [McpConnectorToolItem(**tool) for tool in tools]
    
    # # Convert templates to McpServerTemplateItem objects
    # from datatypes import McpServerTemplateItem
    # templates_config = [McpServerTemplateItem(**template) for template in templates]

    connector_data = {
        "url": request.connector_url,
        "description": connector_data.get("description", "No description available"),
        "version": connector_data.get("version", "1.0.0"),
        "source_logo_url": connector_data.get("logo_url", "").encode() if connector_data.get("logo_url") else b"",
        "logo_url": connector_data.get("logo_url", ""),
        "name": name,
        "tools_config": tools,
        "templates_config": templates,
        "server_config": server_config
    }
    data = create_connector_record(connector_data, session, current_user.id)
    logo_url = connector_data.get("logo_url", "")
    if logo_url and logo_url.strip():
        try:
            store_logo(logo_url, data.name)
        except Exception as e:
            print(f"Warning: Failed to store logo: {str(e)}")
            # Continue without failing the entire request
    
    return {
        "id": data.id,
        "name": data.name,
        "url": data.url,
        "description": data.description,
        "version": data.version,
        "created_at": data.created_at.isoformat(),
        "updated_at": data.updated_at.isoformat(),
        "is_active": data.is_active
    }


@router.get("/connector-schema/{connector_id}")
def get_connector_schema_endpoint(
    connector_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(current_active_user)
) -> dict:
    # Check if user has access to this connector
    connector = check_connector_access(session, current_user, connector_id)
    return connector.server_config


@router.post("/connectors/grant-access")
def grant_connector_access(
    request: GrantConnectorAccessRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_superuser())
) -> dict:
    """Grant a user access to a connector. Only superusers can do this."""
    
    # Verify the connector exists
    connector = session.get(McpConnector, request.connector_id)
    if not connector or not connector.is_active:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    # Verify the user exists
    user = session.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if access already exists
    existing_access = session.exec(
        select(ConnectorAccess).where(
            ConnectorAccess.connector_id == request.connector_id,
            ConnectorAccess.user_id == request.user_id,
            ConnectorAccess.is_active.is_(True)
        )
    ).first()
    
    if existing_access:
        raise HTTPException(
            status_code=400, 
            detail="User already has access to this connector"
        )
    
    # Create new access record
    access = ConnectorAccess(
        connector_id=request.connector_id,
        user_id=request.user_id,
        granted_by=current_user.id
    )
    session.add(access)
    session.commit()
    session.refresh(access)
    
    return {
        "status": "success",
        "message": f"Access granted to user {user.email} for connector {connector.name}",
        "access_id": access.id
    }


@router.post("/connectors/revoke-access")
def revoke_connector_access(
    request: RevokeConnectorAccessRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_superuser())
) -> dict:
    """Revoke a user's access to a connector. Only superusers can do this."""
    
    # Find the access record
    access = session.exec(
        select(ConnectorAccess).where(
            ConnectorAccess.connector_id == request.connector_id,
            ConnectorAccess.user_id == request.user_id,
            ConnectorAccess.is_active.is_(True)
        )
    ).first()
    
    if not access:
        raise HTTPException(
            status_code=404, 
            detail="Access record not found"
        )
    
    # Mark as inactive
    access.is_active = False
    access.updated_at = datetime.utcnow()
    session.add(access)
    session.commit()
    
    return {
        "status": "success",
        "message": f"Access revoked for user {request.user_id} from connector {request.connector_id}"
    }


@router.get("/connectors/{connector_id}/access")
def get_connector_access(
    connector_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_superuser())
) -> List[dict]:
    """Get all users who have access to a connector. Only superusers can do this."""
    
    # Verify the connector exists
    connector = session.get(McpConnector, connector_id)
    if not connector or not connector.is_active:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    # Get all access records for this connector
    access_records = session.exec(
        select(ConnectorAccess).where(
            ConnectorAccess.connector_id == connector_id,
            ConnectorAccess.is_active.is_(True)
        )
    ).all()
    
    result = []
    for access in access_records:
        user = session.get(User, access.user_id)
        granted_by_user = session.get(User, access.granted_by)
        
        result.append({
            "id": access.id,
            "user_id": access.user_id,
            "user_email": user.email if user else "Unknown",
            "granted_by": access.granted_by,
            "granted_by_email": granted_by_user.email if granted_by_user else "Unknown",
            "created_at": access.created_at.isoformat(),
            "updated_at": access.updated_at.isoformat()
        })
    
    return result


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: uuid.UUID,
    request: UpdateUserRoleRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_superuser())
) -> dict:
    """Update a user's superuser status. Only superusers can do this."""
    
    # Get the target user
    target_user = session.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update the superuser status
    target_user.is_superuser = request.is_superuser
    session.add(target_user)
    session.commit()
    session.refresh(target_user)
    
    role_text = "superuser" if request.is_superuser else "regular user"
    return {
        "status": "success",
        "message": f"User {target_user.email} role updated to {role_text}",
        "user_id": str(user_id),
        "is_superuser": target_user.is_superuser
    }


@router.get("/users")
def list_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_superuser())
) -> List[dict]:
    """List all users. Only superusers can do this."""
    
    try:
        users = session.exec(select(User)).all()
        
        result = []
        for user in users:
            # Safely get user attributes
            user_data = {
                "id": str(user.id),
                "email": user.email,
                "is_active": getattr(user, 'is_active', True),
                "is_superuser": getattr(user, 'is_superuser', False),
                "is_verified": getattr(user, 'is_verified', False),
            }
            
            # Add optional fields if they exist
            if hasattr(user, 'created_at') and user.created_at:
                user_data["created_at"] = user.created_at.isoformat()
            if hasattr(user, 'updated_at') and user.updated_at:
                user_data["updated_at"] = user.updated_at.isoformat()
            
            result.append(user_data)
        
        return result
        
    except Exception as e:
        print(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list users"
        )


@router.get("/users/search")
def search_users(
    q: str = Query(..., description="Search query for user email"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_superuser())
) -> List[dict]:
    """Search users by email. Only superusers can do this."""
    
    if not q or len(q.strip()) < 2:
        raise HTTPException(
            status_code=400,
            detail="Search query must be at least 2 characters long"
        )
    
    try:
        # Search for users by email (case-insensitive)
        users = session.exec(
            select(User).where(User.email.ilike(f"%{q.strip()}%"))
        ).all()
        
        result = []
        for user in users:
            # Safely get user attributes
            user_data = {
                "id": str(user.id),
                "email": user.email,
                "is_active": getattr(user, 'is_active', True),
                "is_superuser": getattr(user, 'is_superuser', False),
                "is_verified": getattr(user, 'is_verified', False),
            }
            
            # Add optional fields if they exist
            if hasattr(user, 'created_at') and user.created_at:
                user_data["created_at"] = user.created_at.isoformat()
            
            result.append(user_data)
        
        return result
        
    except Exception as e:
        print(f"Error searching users: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to search users"
        )


@router.post("/servers")
def create_server(
    server_data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(current_active_user)
) -> dict:
    # Ensure connector_id and server_name are provided
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
    
    if "connector_id" not in server_data:
        raise HTTPException(status_code=400, detail="connector_id is required")
    
    connector_id = server_data.pop("connector_id")
    
    # Check if user has access to this connector
    connector = check_connector_access(session, current_user, connector_id)
    
    mcp_server = McpServer(**server_data, connector_id=connector_id, user_id=current_user.id)
    session.add(mcp_server)
    session.commit()
    session.refresh(mcp_server)
    
    tools_list = connector.tools_config

    for tool in tools_list:
        tool = McpServerToolItem(**tool)
        server_tool = McpServerTool(
            mcp_server_id=mcp_server.id,
            user_id=current_user.id,
            name=tool.name,
            tool=tool.model_dump(),
            tool_type=ToolType.static.value,
            is_active=True
        )
        session.add(server_tool)

    session.commit()
    # Generate a secure token
    token_value = f"mcp_token_{secrets.token_urlsafe(32)}"
    token = McpServerToken(
        token=token_value,
        mcp_server_id=mcp_server.id,
        user_id=current_user.id,
        expires_at=token_expires_at
    )
    session.add(token)
    session.commit()
    session.refresh(token)

    return {
        "status": "created",
        "message": f"Server '{mcp_server.server_name}' created successfully",
        "server_id": mcp_server.id,
        "connector_id": mcp_server.connector_id,
        "server_name": mcp_server.server_name,
        "token": token_value,
        "token_expires_at": token.expires_at.isoformat() if token.expires_at else None
    }


@router.get("/servers")
def list_all_servers(
    session: Session = Depends(get_session),
    current_user: User = Depends(current_active_user)
) -> List[dict]:
    """
    List all active server configurations.
    """
    statement = select(McpServer).where(
        McpServer.is_active.is_(True),
        McpServer.user_id == current_user.id
    ).order_by(McpServer.updated_at.desc())
    
    configs = session.exec(statement).all()
    
    return [
        {
            "id": config.id,
            "connector_id": config.connector_id,
            "server_name": config.server_name,
            "server_url": config.server_url,
            "configuration": config.configuration,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
            "is_active": config.is_active
        }
        for config in configs
    ]


@router.get("/servers/with-tokens")
def get_servers_with_tokens(session: Session = Depends(get_session)) -> List[dict]:
    """
    Retrieve all active MCP servers with their active tokens.
    """
    statement = select(McpServer).where(McpServer.is_active.is_(True))
    servers = session.exec(statement).all()
    
    result = []
    for server in servers:
        # Get active tokens for this server
        token_statement = select(McpServerToken).where(
            McpServerToken.mcp_server_id == server.id,
            McpServerToken.is_active.is_(True)
        )
        tokens = session.exec(token_statement).all()
        
        server_data = {
            "id": server.id,
            "connector_id": server.connector_id,
            "server_name": server.server_name,
            "server_url": server.server_url,
            "created_at": server.created_at.isoformat(),
            "updated_at": server.updated_at.isoformat(),
            "is_active": server.is_active,
            "tokens": [
                {
                    "id": token.id,
                    "token": token.token,
                    "expires_at": token.expires_at.isoformat() if token.expires_at else None,
                    "created_at": token.created_at.isoformat(),
                    "is_active": token.is_active
                }
                for token in tokens
            ]
        }
        result.append(server_data)
    
    return result


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
        "connector_id": config.connector_id,
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
            "connector_id": existing_config.connector_id,
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
        }

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete server: {str(e)}")


@router.get("/servers/{server_id}/tokens")
def get_server_tokens(
    server_id: int,
    session: Session = Depends(get_session)
) -> List[dict]:
    """
    Retrieve all active tokens for a specific server.
    """
    # First check if the server exists
    server_statement = select(McpServer).where(
        McpServer.id == server_id,
        McpServer.is_active.is_(True)
    )
    server = session.exec(server_statement).first()
    
    if not server:
        raise HTTPException(status_code=404, detail=f"No server found with id: {server_id}")
    
    # Get active tokens for this server
    token_statement = select(McpServerToken).where(
        McpServerToken.mcp_server_id == server_id,
        McpServerToken.is_active.is_(True)
    )
    tokens = session.exec(token_statement).all()
    
    return [
        {
            "id": token.id,
            "token": token.token,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "created_at": token.created_at.isoformat(),
            "is_active": token.is_active
        }
        for token in tokens
    ]


@router.get("/servers/{server_id}/tools/database")
def get_database_tools(
    server_id: int,
    session: Session = Depends(get_session)
) -> dict:
    """
    Retrieve tools from database with tool_type information.
    """
    # Get the server configuration
    statement = select(McpServer).where(
        McpServer.id == server_id,
        McpServer.is_active.is_(True)
    )
    server: McpServer = session.exec(statement).first()
    if not server:
        raise HTTPException(status_code=404, detail=f"No server found with id: {server_id}")
    
    # Get all tools from database (both active and inactive for management)
    server_tools: List[McpServerTool] = server.server_tools
    
    if not server_tools:
        return {
            "server_id": server.id,
            "server_name": server.server_name,
            "connector_id": server.connector_id,
            "tools": []
        }
    
    # Transform database tools to MCP format
    tools = []
    for server_tool in server_tools:
        tool = McpServerToolItem(**server_tool.tool)
        tool_type_value = server_tool.tool_type.value if server_tool.tool_type else "static"
        tools.append({
            "id": server_tool.id,
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema if tool.inputSchema else {},
            "tool_type": tool_type_value,  # Show tool_type
            "template_name": server_tool.template_name,
            "template_args": server_tool.template_args,
            "is_active": server_tool.is_active
        })

    return {
        "server_id": server.id,
        "server_name": server.server_name,
        "connector_id": server.connector_id,
        "tools": tools
    }


@router.get("/servers/{server_id}/tools")
def get_server_tools(
    server_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(current_active_user)
) -> dict:
    """
    Retrieve tools from database with tool_type information.
    """
    # Get the server configuration
    statement = select(McpServer).where(
        McpServer.id == server_id,
        McpServer.is_active.is_(True),
        McpServer.user_id == current_user.id
    )
    server: McpServer = session.exec(statement).first()
    if not server:
        raise HTTPException(status_code=404, detail=f"No server found with id: {server_id}")
    
    # Get all tools from database (both active and inactive for management)
    server_tools: List[McpServerTool] = server.server_tools
    
    if not server_tools:
        return {
            "server_id": server.id,
            "server_name": server.server_name,
            "connector_id": server.connector_id,
            "tools": []
        }
    
    # Transform database tools to MCP format
    tools = []
    for server_tool in server_tools:
        tool = McpServerToolItem(**server_tool.tool)
        tool_type_value = server_tool.tool_type.value if server_tool.tool_type else "static"
        tools.append({
            "id": server_tool.id,
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema if tool.inputSchema else {},
            "tool_type": tool_type_value,  # Show tool_type
            "template_name": server_tool.template_name,
            "template_args": server_tool.template_args,
            "is_active": server_tool.is_active
        })

    return {
        "server_id": server.id,
        "server_name": server.server_name,
        "connector_id": server.connector_id,
        "tools": tools
    }


@router.patch("/servers/{server_id}/tools/{tool_id}")
def update_tool_status(
    server_id: int,
    tool_id: int,
    update_data: dict,
    session: Session = Depends(get_session)
) -> dict:
    """
    Update a tool's status (active/inactive).
    """
    try:
        # Verify server exists
        # Get the tool
        tool_statement = select(McpServerTool).where(
            McpServerTool.id == tool_id,
            McpServerTool.mcp_server_id == server_id
        )
        tool = session.exec(tool_statement).first()

        if not tool:
            raise HTTPException(
                status_code=404,
                detail=f"No tool found with id: {tool_id} for server: {server_id}"
            )

        # Update tool status
        if "is_active" in update_data:
            tool.is_active = update_data["is_active"]
            tool.updated_at = datetime.utcnow()
            session.add(tool)
            session.commit()
            session.refresh(tool)

        return {
            "status": "updated",
            "message": f"Tool '{tool.name}' updated successfully",
            "tool_id": tool.id,
            "tool_name": tool.name,
            "is_active": tool.is_active
        }

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update tool: {str(e)}")


@router.delete("/servers/{server_id}/tools/{tool_id}")
def delete_tool(
    server_id: int,
    tool_id: int,
    session: Session = Depends(get_session)
) -> dict:
    """
    Permanently delete a tool from a server.
    Only allows deletion of dynamic tools for safety.
    This action cannot be undone.
    """
    try:
        # Get the tool
        tool_statement = select(McpServerTool).where(
            McpServerTool.id == tool_id,
            McpServerTool.mcp_server_id == server_id
        )
        tool: McpServerTool = session.exec(tool_statement).first()
        if not tool:
            raise HTTPException(status_code=404, detail=f"No tool found with id: {tool_id}")

        # Check if tool is dynamic (only allow deletion of dynamic tools)
        if tool.tool_type != ToolType.dynamic:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete tool '{tool.name}'. Only dynamic tools can be deleted. This tool is of type '{tool.tool_type.value}'."
            )

        # Permanently delete the tool from database
        tool_name = tool.name
        tool_type = tool.tool_type.value
        session.delete(tool)
        session.commit()

        return {
            "status": "deleted",
            "message": f"Dynamic tool '{tool_name}' permanently deleted",
            "tool_id": tool_id,
            "tool_name": tool_name,
            "tool_type": tool_type
        }

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete tool: {str(e)}")


@router.get("/connectors/{connector_id}/templates")
def get_templates(
    connector_id: int,
    session: Session = Depends(get_session)
) -> List[McpConnectorTemplateItem]:
    """
    Create a new tool based on a connector template.
    """
    # Verify connector exists
    connector_statement = select(McpConnector).where(
        McpConnector.id == connector_id,
        McpConnector.is_active.is_(True)
    )
    connector = session.exec(connector_statement).first()
    
    if not connector:
        raise HTTPException(status_code=404, detail=f"Connector with id {connector_id} not found")
    
    # Check if template exists in connector
    templates = connector.templates_config or []
    return templates


@router.post("/servers/{server_id}/tools")
def create_tool_from_template(
    server_id: int,
    tool_data: dict,
    session: Session = Depends(get_session)
) -> McpServerToolItem:
    """
    Create a new tool based on a connector template.
    """
    tool = McpServerToolItem(**tool_data)
    
    # Extract template information from tool_data if present
    template_name = tool_data.get('template_name')
    template_args = tool_data.get('template_args', {})
    
    server_tool = McpServerTool(
        mcp_server_id=server_id,
        name=tool.name,
        template_name=template_name,
        template_args=template_args,
        tool=tool.model_dump(),
        tool_type=ToolType.dynamic.value,
        is_active=True
    )
    session.add(server_tool)
    session.commit()
    return server_tool.tool


# verify auth token api endpoint
@router.get("/verify-auth-token")
def verify_auth_token(
    auth: McpServerToken = Depends(get_auth_token)
) -> dict:
    return {"status": "verified", "message": "Auth token verified successfully"}


@app.get("/.well-known/oauth-authorization-server")
def get_oauth_authorization_server() -> dict:
    return {
        "issuer": "https://auth.example.com",
        "authorization_endpoint": "https://auth.example.com/oauth/authorize",
        "token_endpoint": "https://auth.example.com/oauth/token",
        "userinfo_endpoint": "https://auth.example.com/oauth/userinfo",
        "jwks_uri": "https://auth.example.com/.well-known/jwks.json",
        "scopes_supported": ["openid", "profile", "email", "read", "write"],
        "response_types_supported": ["code", "token", "id_token"],
        "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token"],
        "subject_types_supported": ["public", "pairwise"],
        "id_token_signing_alg_values_supported": ["RS256", "ES256"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
        "claims_supported": ["sub", "iss", "aud", "exp", "iat", "name", "email"],
        "code_challenge_methods_supported": ["S256", "plain"]
    }


@app.get("/.well-known/oauth-protected-resource")
def get_oauth_authorization_server() -> dict:
    return {
        "issuer": "https://auth.example.com",
        "authorization_endpoint": "https://auth.example.com/oauth/authorize",
        "token_endpoint": "https://auth.example.com/oauth/token",
        "userinfo_endpoint": "https://auth.example.com/oauth/userinfo",
        "jwks_uri": "https://auth.example.com/.well-known/jwks.json",
        "scopes_supported": ["openid", "profile", "email", "read", "write"],
        "response_types_supported": ["code", "token", "id_token"],
        "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token"],
        "subject_types_supported": ["public", "pairwise"],
        "id_token_signing_alg_values_supported": ["RS256", "ES256"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
        "claims_supported": ["sub", "iss", "aud", "exp", "iat", "name", "email"],
        "code_challenge_methods_supported": ["S256", "plain"]
    }


@router.get("/tools")
def get_tools(
    session: Session = Depends(get_session),
    token: McpServerToken = Depends(get_auth_token)
) -> List[Dict[str, Any]]:
    """
    Get all tools from database.
    """
    server_tools = session.exec(
        select(McpServerTool).where(
            McpServerTool.mcp_server_id == token.mcp_server_id,
            McpServerTool.is_active.is_(True)
        )).all()
    tools = []
    print(f"Server tools: {len(server_tools)}")
    print(f"Server ID: {token.mcp_server_id}")
    for server_tool in server_tools:
        tool_data = {
            'tool_type': server_tool.tool_type,
            'template_name': server_tool.template_name,
            'template_args': server_tool.template_args,
            'tool': server_tool.tool
        }
        tools.append(tool_data)
    return tools


@router.get("/tool")
def get_tool_by_name(
    name: str = Query(default=""),
    session: Session = Depends(get_session),
    token: McpServerToken = Depends(get_auth_token)
) -> Dict[str, Any]:
    """
    Get a tool by name from database.
    """
    tool = session.exec(
        select(McpServerTool).where(
            McpServerTool.mcp_server_id == token.mcp_server_id,
            McpServerTool.is_active.is_(True),
            McpServerTool.name == name
        )).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"No tool found with name: {name}")
    tool_data = {
        'tool_type': tool.tool_type,
        'name': tool.name,
        'template_name': tool.template_name,
        'template_args': tool.template_args,
        'tool': tool.tool
    }
    return tool_data


app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)
