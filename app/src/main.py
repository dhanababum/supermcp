import os
from re import S
import httpx
import requests
import bcrypt
import jwt
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from starlette.responses import FileResponse
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List

from src.config import settings
from src.database import get_async_session
from src.utils import get_logo, store_logo
from src.datatypes import (
    McpServerToolItem,
    ToolType,
    McpConnectorTemplateItem,
    ConnectorMode,
    UserCreate,
    UserRead,
    UserUpdate,
    RegisterRequest,
    RegisterConnectorRequest,
    CreateConnectorRequest,
    GrantConnectorAccessRequest,
    RevokeConnectorAccessRequest,
)
from src.users import (
    jwt_auth_backend,
    cookie_auth_backend,
    current_active_user,
    fastapi_users,
)
from src.models import (
    McpConnector,
    McpServer,
    McpServerToken,
    McpServerTool,
    User,
    ConnectorAccess,
)


app = FastAPI(title="MCP Tools API", description="API for MCP Tools", version="0.1.0")


token_header = HTTPBearer()
APP_MEDIA_PATH = os.path.join(settings.APP_STORAGE_PATH, "media")


# create auth dependency & verify with McpServerToken
async def get_auth_token(
    token: HTTPAuthorizationCredentials = Depends(token_header),
    session: AsyncSession = Depends(get_async_session),
):
    print(f"Verifying token: {token.credentials}")
    token_statement = select(McpServerToken).where(
        McpServerToken.token == token.credentials, McpServerToken.is_active.is_(True)
    )
    server_token = await session.execute(token_statement)
    server_token: McpServerToken = server_token.scalars().first()
    print(f"Token: {type(server_token)}")
    if not server_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    print("..........")
    return server_token


async def get_token(server_id: str):
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=15)
    token = jwt.encode(
        {
            "sub": f"server:{server_id}",
            "iat": now.timestamp(),
            "exp": exp.timestamp(),
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGO,
    )

    return {"access_token": token, "expires_at": exp.isoformat()}


async def verify_token(
    token: HTTPAuthorizationCredentials = Depends(token_header)
):
    try:
        payload = jwt.decode(
            token.credentials, settings.JWT_SECRET, algorithms=[settings.JWT_ALGO])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def verify_connector_token(
    connector_id: str,
    token: HTTPAuthorizationCredentials = Depends(token_header),
    session: AsyncSession = Depends(get_async_session),
) -> McpConnector | None:
    secret_hash = bcrypt.hashpw(
        token.credentials.encode(), settings.CONNECTOR_SALT.encode())
    connector = await session.execute(
        select(McpConnector).where(
            McpConnector.id == connector_id,
            McpConnector.secret == secret_hash
        )
    )
    connector: McpConnector = connector.scalars().first()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    return connector


async def get_all_connectors(session: AsyncSession):
    connectors = await session.execute(select(McpConnector))
    connectors = connectors.scalars().all()
    return connectors


def is_superuser(user: User) -> bool:
    """Check if user has superuser role using fastapi-users built-in field."""
    return user.is_superuser


def check_superuser_access(user: User):
    """Raise HTTPException if user is not a superuser."""
    if not is_superuser(user):
        raise HTTPException(
            status_code=403, detail="Access denied. Superuser role required."
        )


def require_superuser():
    """FastAPI dependency that requires superuser access."""

    def superuser_dependency(user: User = Depends(current_active_user)):
        check_superuser_access(user)
        return user

    return superuser_dependency


async def get_user_accessible_connectors(
    session: AsyncSession, user: User
) -> List[McpConnector]:
    """Get connectors that the user has access to."""
    if is_superuser(user):
        # Superusers can see all connectors
        result = await session.execute(
            select(McpConnector).where(McpConnector.is_active.is_(True))
        )
        return result.scalars().all()
    else:
        # Regular users can only see connectors they have access to
        statement = (
            select(McpConnector)
            .join(ConnectorAccess)
            .where(
                ConnectorAccess.user_id == user.id,
                ConnectorAccess.is_active.is_(True),
                McpConnector.is_active.is_(True),
            )
        )
        result = await session.execute(statement)
        return result.scalars().all()


async def check_connector_access(
    session: AsyncSession, user: User, connector_id: int
) -> McpConnector:
    """Check if user has access to a specific connector and return it."""
    if is_superuser(user):
        # Superusers can access any connector
        connector = await session.get(McpConnector, connector_id)
        if not connector or not connector.is_active:
            raise HTTPException(status_code=404, detail="Connector not found")
        return connector
    else:
        # Regular users need explicit access
        statement = (
            select(McpConnector)
            .join(ConnectorAccess)
            .where(
                McpConnector.id == connector_id,
                ConnectorAccess.user_id == user.id,
                ConnectorAccess.is_active.is_(True),
                McpConnector.is_active.is_(True),
            )
        )
        connector = await session.execute(statement)
        connector: McpConnector = connector.scalars().first()
        if not connector:
            raise HTTPException(
                status_code=403,
                detail="Access denied. You don't have access to this connector.",
            )
        return connector


async def create_connector_record(
    connector_data: dict, session: AsyncSession, user_id: uuid.UUID = None
):
    if user_id:
        connector_data["created_by"] = user_id
    connector = McpConnector(**connector_data)
    session.add(connector)
    await session.commit()
    await session.refresh(connector)
    return connector


# Add CORS middleware to allow requests from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.WEB_URL],  # React dev server
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
    fastapi_users.get_auth_router(cookie_auth_backend),
    prefix="/auth/cookie",
    tags=["auth"],
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


@router.get("/quick-token-verify")
async def quick_token_verify(_: str = Depends(verify_token)):
    return {"message": "Token verified"}


@router.get(
    "/connectors/{connector_logo}",
    response_class=FileResponse,
)
async def get_connector_logo(connector_logo: str):
    try:
        return await get_logo(APP_MEDIA_PATH, connector_logo)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Logo not found: {connector_logo}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading logo: {str(e)}")


@router.get("/connectors")
async def get_connectors(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> list:
    try:
        # Get connectors based on user role and access
        connectors = await get_user_accessible_connectors(session, current_user)

        # Convert to dict to avoid relationship serialization issues
        result = []
        for connector in connectors:
            result.append(
                {
                    "id": connector.id,
                    "name": connector.name,
                    "url": connector.url,
                    "description": connector.description,
                    "version": connector.version,
                    "logo_name": connector.logo_name,
                    "mode": (
                        connector.mode
                        if isinstance(connector.mode, str)
                        else connector.mode.value
                    ),
                    "created_at": (
                        connector.created_at.isoformat()
                        if connector.created_at
                        else None
                    ),
                    "updated_at": (
                        connector.updated_at.isoformat()
                        if connector.updated_at
                        else None
                    ),
                    "is_active": connector.is_active,
                }
            )

        return result
    except Exception as e:
        print(f"Error in get_connectors: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# get all active servers based on connector id
@router.get("/connectors/{connector_id}/servers")
async def get_servers(
    connector: McpConnector = Depends(verify_connector_token),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get all active servers based on connector id.
    """
    result = await session.execute(
        select(McpServer).where(
            McpServer.connector_id == connector.id,
            McpServer.is_active.is_(True)
        )
    )
    servers = result.scalars().all()
    return {
        server.id: server.configuration for server in servers}


@router.get("/connectors/{connector_id}/servers/{server_id}")
async def get_server(
    server_id: str,
    connector: McpConnector = Depends(verify_connector_token),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get a specific server based on connector id and server id.
    """
    result = await session.execute(
        select(McpServer).where(
            McpServer.connector_id == connector.id,
            McpServer.id == server_id,
            McpServer.is_active.is_(True)
        )
    )
    server = result.scalars().first()
    return server.configuration


@router.post("/connectors/register")
async def register_connector(
    request: RegisterConnectorRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_superuser()),
) -> dict:
    """
    Step 1: Register a connector with basic metadata.
    This creates a connector record in 'deactive' mode.
    The connector will be activated later when the connector server is running.
    Only superusers can register connectors.
    """
    try:
        # Check if connector with this name already exists
        existing = await session.execute(
            select(McpConnector).where(
                McpConnector.name == request.name,
                McpConnector.is_active.is_(True)
            )
        )
        existing = existing.scalars().first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Connector with name '{request.name}' already exists",
            )

        # Generate a unique secret for the connector
        secret_plain = uuid.uuid4().hex  # Generate a random secret
        print(f"Secret plain: {secret_plain}")
        print(f"Connector salt: {settings.CONNECTOR_SALT}")
        secret_hash = bcrypt.hashpw(
            secret_plain.encode(), settings.CONNECTOR_SALT.encode())

        # Create connector in deactive mode
        connector_data = {
            "name": request.name,
            "url": "",
            "description": request.description,
            "version": "0.0.0",
            "source_logo_url": b"",
            "logo_name": "",
            "mode": ConnectorMode.sync.value,
            "secret": secret_hash,
            "tools_config": [],
            "templates_config": [],
            "server_config": {},
            "is_active": True,
        }

        connector = await create_connector_record(
            connector_data, session, current_user.id)

        return {
            "status": "registered",
            "message": f"Connector '{connector.name}' registered successfully",
            "connector_id": str(connector.id),
            "secret": secret_plain,
            "name": connector.name,
            "mode": (
                connector.mode.value
                if hasattr(connector.mode, "value")
                else connector.mode
            ),
            "description": connector.description,
            "created_at": connector.created_at.isoformat(),
            "next_step": "Activate the connector by providing the connector URL via POST /api/connectors/activate",
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to register connector: {str(e)}"
        )


@router.post("/connectors/activate")
async def activate_connector(
    request: CreateConnectorRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_superuser()),
) -> dict:
    """
    Step 2: Activate a registered connector by fetching its schema from the connector URL.
    This updates the connector with actual configuration and changes mode to 'active'.
    Only superusers can activate connectors.
    """
    try:
        # Get the registered connector
        connector = await session.execute(select(McpConnector).where(
            McpConnector.id == request.connector_id))
        connector: McpConnector = connector.scalars().first()

        if not connector:
            raise HTTPException(
                status_code=404,
                detail=f"Connector with ID {request.connector_id} not found",
            )

        if not connector.is_active:
            raise HTTPException(
                status_code=400, detail=f"Connector '{connector.name}' is not active"
            )

        # Fetch connector schema from URL
        try:
            async with httpx.AsyncClient() as client:
                req = await client.get(f"{request.connector_url}/connector.json", timeout=10)
                if req.status_code != 200:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to fetch connector schema from {request.connector_url}. Status: {req.status_code}",
                    )
                connector_data = req.json()
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to fetch connector schema: {str(e)}"
            )

        # Extract schema data
        name = connector_data.get("name", connector.name)
        tools = connector_data.get("tools", [])
        templates = connector_data.get("templates", {})
        server_config = connector_data.get("config", {})
        version = connector_data.get("version", "1.0.0")
        description = connector_data.get("description", connector.description)
        logo_url = connector_data.get("logo_url", "")

        # Update connector with fetched data
        connector.url = request.connector_url
        connector.description = description
        connector.version = version
        connector.source_logo_url = logo_url.encode() if logo_url else b""
        connector.tools_config = tools
        connector.templates_config = templates
        connector.server_config = server_config
        connector.mode = ConnectorMode.active.value
        connector.updated_at = datetime.utcnow()

        session.add(connector)
        await session.commit()
        await session.refresh(connector)

        # Store logo if available
        if logo_url and logo_url.strip():
            try:
                logo_name = await store_logo(
                    f"{connector.url}{logo_url}", APP_MEDIA_PATH, f"connector_{connector.id}")
                # Ensure logo_name is never None (use empty string as fallback)
                connector.logo_name = logo_name if logo_name else ""
                session.add(connector)
                await session.commit()
                await session.refresh(connector)
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to store logo: {str(e)}")

        return {
            "status": "activated",
            "message": f"Connector '{connector.name}' activated successfully",
            "connector_id": connector.id,
            "name": connector.name,
            "url": connector.url,
            "mode": (
                connector.mode.value
                if hasattr(connector.mode, "value")
                else connector.mode
            ),
            "version": connector.version,
            "tools_count": len(tools),
            "templates_count": (
                len(templates)
                if isinstance(templates, list)
                else len(templates.keys()) if isinstance(templates, dict) else 0
            ),
            "created_at": connector.created_at.isoformat(),
            "updated_at": connector.updated_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to activate connector: {str(e)}"
        )


@router.patch("/connectors/{connector_id}/mode")
async def update_connector_mode(
    connector_id: uuid.UUID,
    request: dict,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_superuser()),
) -> dict:
    """
    Update connector mode (active/deactive toggle).
    Only superusers can update connector mode.
    """
    try:
        # Get the connector
        connector = await session.get(McpConnector, connector_id)

        if not connector:
            raise HTTPException(
                status_code=404, detail=f"Connector with ID {connector_id} not found"
            )

        # Get the new mode from request
        new_mode = request.get("mode")
        if not new_mode:
            raise HTTPException(status_code=400, detail="Mode field is required")

        # Validate mode value
        valid_modes = ["active", "deactive", "sync"]
        if new_mode not in valid_modes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mode. Must be one of: {', '.join(valid_modes)}",
            )

        # Update the mode
        connector.mode = new_mode
        connector.updated_at = datetime.utcnow()

        session.add(connector)
        await session.commit()
        await session.refresh(connector)

        return {
            "status": "success",
            "message": f"Connector mode updated to {new_mode}",
            "connector": {
                "id": str(connector.id),
                "name": connector.name,
                "mode": (
                    connector.mode
                    if isinstance(connector.mode, str)
                    else connector.mode.value
                ),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update connector mode: {str(e)}"
        )


@router.delete("/connectors/{connector_id}")
async def delete_connector(
    connector_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_superuser()),
) -> dict:
    """
    Delete a connector (hard delete). Only superusers can do this.
    Database CASCADE DELETE will automatically remove:
    - All servers using this connector (via FK CASCADE on mcp_servers.connector_id)
    - All user access grants (via FK CASCADE on connector_access.connector_id)
    """
    try:
        # Get the connector
        connector = await session.get(McpConnector, connector_id)

        if not connector:
            raise HTTPException(
                status_code=404, detail=f"Connector with id {connector_id} not found"
            )

        # Count affected resources before deletion (for reporting)
        access_count = await session.execute(
                select(func.count(ConnectorAccess.id)).where(
                    ConnectorAccess.connector_id == connector_id,
                    ConnectorAccess.is_active.is_(True),
                )
            )
        access_count = access_count.scalars()

        servers_count = await session.execute(
                select(func.count(McpServer.id)).where(
                    McpServer.connector_id == connector_id,
                    McpServer.is_active.is_(True),
                )
            )
        servers_count = servers_count.scalars()

        connector_name = connector.name

        # Delete the connector using direct SQL to ensure CASCADE DELETE works properly
        # This bypasses SQLAlchemy's relationship management that might try to set FK to NULL
        from sqlalchemy import text

        await session.execute(
            text("DELETE FROM mcp_connectors WHERE id = :connector_id"),
            {"connector_id": connector_id},
        )
        await session.commit()

        return {
            "status": "deleted",
            "message": f"Connector '{connector_name}' and all related data deleted successfully",
            "connector_id": connector_id,
            "revoked_access": access_count,
            "deleted_servers": servers_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to delete connector: {str(e)}"
        )


@router.get("/connector-schema/{connector_id}")
async def get_connector_schema_endpoint(
    connector_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> dict:
    # Check if user has access to this connector
    connector = await check_connector_access(
        session, current_user, connector_id)
    return connector.server_config


@router.post("/connectors/grant-access")
async def grant_connector_access(
    request: GrantConnectorAccessRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_superuser()),
) -> dict:
    """Grant a user access to a connector. Only superusers can do this."""

    # Verify the connector exists
    connector = await session.get(McpConnector, request.connector_id)
    if not connector or not connector.is_active:
        raise HTTPException(status_code=404, detail="Connector not found")

    # Verify the user exists
    user = await session.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if access already exists
    existing_access = await session.execute(
        select(ConnectorAccess).where(
            ConnectorAccess.connector_id == request.connector_id,
            ConnectorAccess.user_id == request.user_id,
            ConnectorAccess.is_active.is_(True),
        )
    )
    existing_access: ConnectorAccess = existing_access.scalars().first()

    if existing_access:
        raise HTTPException(
            status_code=400, detail="User already has access to this connector"
        )

    # Create new access record
    access = ConnectorAccess(
        connector_id=request.connector_id,
        user_id=request.user_id,
        granted_by=current_user.id,
    )
    session.add(access)
    await session.commit()
    await session.refresh(access)

    return {
        "status": "success",
        "message": f"Access granted to user {user.email} for connector {connector.name}",
        "access_id": access.id,
    }


@router.post("/connectors/revoke-access")
async def revoke_connector_access(
    request: RevokeConnectorAccessRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_superuser()),
) -> dict:
    """Revoke a user's access to a connector. Only superusers can do this."""

    # Find the access record
    access = await session.execute(
        select(ConnectorAccess).where(
            ConnectorAccess.connector_id == request.connector_id,
            ConnectorAccess.user_id == request.user_id,
            ConnectorAccess.is_active.is_(True),
        )
    )
    access: ConnectorAccess = access.scalars().first()

    if not access:
        raise HTTPException(status_code=404, detail="Access record not found")

    # Mark as inactive
    access.is_active = False
    access.updated_at = datetime.utcnow()
    session.add(access)
    await session.commit()

    return {
        "status": "success",
        "message": f"Access revoked for user {request.user_id} from connector {request.connector_id}",
    }


@router.get("/connectors/{connector_id}/access")
async def get_connector_access(
    connector_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_superuser()),
) -> List[dict]:
    """Get all users who have access to a connector. Only superusers can do this."""

    # Verify the connector exists
    connector = await session.get(McpConnector, connector_id)
    if not connector or not connector.is_active:
        raise HTTPException(status_code=404, detail="Connector not found")

    # Get all access records for this connector
    access_records = await session.execute(
        select(ConnectorAccess).where(
            ConnectorAccess.connector_id == connector_id,
            ConnectorAccess.is_active.is_(True),
        )
    )
    access_records = access_records.scalars().all()

    result = []
    for access in access_records:
        user = await session.get(User, access.user_id)
        granted_by_user = await session.get(User, access.granted_by)

        result.append(
            {
                "id": access.id,
                "user_id": access.user_id,
                "user_email": user.email if user else "Unknown",
                "granted_by": access.granted_by,
                "granted_by_email": (
                    granted_by_user.email if granted_by_user else "Unknown"
                ),
                "created_at": access.created_at.isoformat(),
                "updated_at": access.updated_at.isoformat(),
            }
        )

    return result


@router.get("/users")
async def list_users(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_superuser()),
) -> List[dict]:
    """List all users. Only superusers can do this."""

    try:
        users = await session.execute(select(User))
        users = users.scalars().all()

        result = []
        for user in users:
            # Safely get user attributes
            user_data = {
                "id": str(user.id),
                "email": user.email,
                "is_active": getattr(user, "is_active", True),
                "is_superuser": getattr(user, "is_superuser", False),
                "is_verified": getattr(user, "is_verified", False),
            }

            # Add optional fields if they exist
            if hasattr(user, "created_at") and user.created_at:
                user_data["created_at"] = user.created_at.isoformat()
            if hasattr(user, "updated_at") and user.updated_at:
                user_data["updated_at"] = user.updated_at.isoformat()

            result.append(user_data)

        return result

    except Exception as e:
        print(f"Error listing users: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list users")


@router.get("/users/search")
async def search_users(
    q: str = Query(..., description="Search query for user email"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_superuser()),
) -> List[dict]:
    """Search users by email. Only superusers can do this."""

    if not q or len(q.strip()) < 2:
        raise HTTPException(
            status_code=400, detail="Search query must be at least 2 characters long"
        )

    try:
        # Search for users by email (case-insensitive)
        users = await session.execute(
            select(User).where(User.email.ilike(f"%{q.strip()}%"))
        )
        users = users.scalars().all()

        result = []
        for user in users:
            # Safely get user attributes
            user_data = {
                "id": str(user.id),
                "email": user.email,
                "is_active": getattr(user, "is_active", True),
                "is_superuser": getattr(user, "is_superuser", False),
                "is_verified": getattr(user, "is_verified", False),
            }

            # Add optional fields if they exist
            if hasattr(user, "created_at") and user.created_at:
                user_data["created_at"] = user.created_at.isoformat()

            result.append(user_data)

        return result

    except Exception as e:
        print(f"Error searching users: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search users")


@router.post("/servers")
async def create_server(
    server_data: dict,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
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
                    status_code=400, detail="Invalid token_expires_at format"
                )

    if "connector_id" not in server_data:
        raise HTTPException(status_code=400, detail="connector_id is required")

    connector_id = server_data.pop("connector_id")

    # Check if user has access to this connector
    connector = await check_connector_access(
        session, current_user, connector_id)
    server_data["server_url"] = connector.url
    mcp_server = McpServer(
        **server_data, connector_id=connector_id, user_id=current_user.id
    )
    session.add(mcp_server)
    await session.commit()
    await session.refresh(mcp_server)

    tools_list = connector.tools_config

    for tool in tools_list:
        tool = McpServerToolItem(**tool)
        server_tool = McpServerTool(
            mcp_server_id=mcp_server.id,
            user_id=current_user.id,
            name=tool.name,
            tool=tool.model_dump(),
            tool_type=ToolType.static.value,
            is_active=True,
        )
        session.add(server_tool)

    await session.commit()
    # Generate a secure token
    token_value = f"mcp_token_{secrets.token_urlsafe(32)}"
    token = McpServerToken(
        token=token_value,
        mcp_server_id=mcp_server.id,
        user_id=current_user.id,
        expires_at=token_expires_at,
    )
    session.add(token)
    await session.commit()
    await session.refresh(token)

    token_data = await get_token(mcp_server.id)

    async with httpx.AsyncClient(timeout=100) as client:

        response = await client.post(
            f"{mcp_server.server_url}/create-server/{mcp_server.id}",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        print(response)
        # print(response.json())

    return {
        "status": "created",
        "message": f"Server '{mcp_server.server_name}' created successfully",
        "server_id": mcp_server.id,
        "connector_id": mcp_server.connector_id,
        "server_name": mcp_server.server_name,
        "token": token_value,
        "token_expires_at": token.expires_at.isoformat() if token.expires_at else None,
    }


@router.get("/servers")
async def list_all_servers(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> List[dict]:
    """
    List all active server configurations.
    """
    statement = (
        select(McpServer)
        .where(
            McpServer.is_active.is_(True),
            McpServer.user_id == current_user.id)
        .order_by(McpServer.updated_at.desc())
    )
    result = await session.execute(statement)
    configs = result.scalars().all()

    return [
        {
            "id": config.id,
            "connector_id": config.connector_id,
            "server_name": config.server_name,
            "server_url": config.server_url,
            "configuration": config.configuration,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
            "is_active": config.is_active,
        }
        for config in configs
    ]


@router.get("/servers/with-tokens")
async def get_servers_with_tokens(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> List[dict]:
    """
    Retrieve all active MCP servers with their active tokens.
    """
    statement = select(McpServer).where(
        McpServer.is_active.is_(True),
        McpServer.user_id == current_user.id,
    )
    servers = await session.execute(statement)
    servers = servers.scalars().all()

    result = []
    for server in servers:
        # Get active tokens for this server
        token_statement = select(McpServerToken).where(
            McpServerToken.mcp_server_id == server.id,
            McpServerToken.is_active.is_(True),
        )
        tokens = await session.execute(token_statement)
        tokens = tokens.scalars().all()

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
                    "expires_at": (
                        token.expires_at.isoformat() if token.expires_at else None
                    ),
                    "created_at": token.created_at.isoformat(),
                    "is_active": token.is_active,
                }
                for token in tokens
            ],
        }
        result.append(server_data)

    return result


@router.get("/servers/{server_id}")
async def get_server(
    server_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> dict:
    """
    Retrieve the active configuration for a specific server.
    """
    statement = select(McpServer).where(
        McpServer.id == server_id, McpServer.is_active.is_(True), McpServer.user_id == current_user.id,
    )
    config = await session.execute(statement)
    config: McpServer = config.scalars().first()

    if not config:
        raise HTTPException(
            status_code=404, detail=f"No server found with id: {server_id}"
        )

    return {
        "id": config.id,
        "connector_id": config.connector_id,
        "server_name": config.server_name,
        "configuration": config.configuration,
        "created_at": config.created_at.isoformat(),
        "updated_at": config.updated_at.isoformat(),
        "is_active": config.is_active,
    }


@router.put("/servers/{server_id}")
async def update_server(
    server_id: str,
    config_data: dict,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> dict:
    """
    Save or update a server configuration.
    Uses JSONB to store dynamic schema data.
    """
    try:
        # Check if configuration already exists for this server
        statement = select(McpServer).where(
            McpServer.id == server_id, McpServer.is_active.is_(True)
        )
        existing_config = await session.execute(statement)
        existing_config: McpServer = existing_config.scalars().first()

        if not existing_config:
            raise HTTPException(
                status_code=404, detail=f"No server found with id: {server_id}"
            )

        # Update existing configuration
        existing_config.configuration = config_data
        existing_config.updated_at = datetime.utcnow()
        session.add(existing_config)
        await session.commit()
        session.refresh(existing_config)

        return {
            "status": "updated",
            "message": f"Configuration for server '{existing_config.server_name}' updated successfully",
            "server_id": existing_config.id,
            "connector_id": existing_config.connector_id,
            "server_name": existing_config.server_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update server: {str(e)}"
        )


@router.delete("/servers/{server_id}")
async def delete_server(
    server_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> dict:
    """
    Soft delete a server configuration and all related data (marks as inactive).
    This includes the server, all its tokens, and all its tools.
    """
    try:
        # Get the server
        statement = select(McpServer).where(
            McpServer.id == server_id, McpServer.is_active.is_(True), McpServer.user_id == current_user.id,
        )
        server = await session.execute(statement)
        server: McpServer = server.scalars().first()
        if not server:
            raise HTTPException(
                status_code=404, detail=f"No server found with id: {server_id}"
            )

        # Mark all related tokens as inactive
        token_statement = select(McpServerToken).where(
            McpServerToken.mcp_server_id == server_id,
            McpServerToken.is_active.is_(True),
        )
        tokens = await session.execute(token_statement)
        tokens = tokens.scalars().all()
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
        await session.commit()

        return {
            "status": "deleted",
            "message": f"Server '{server.server_name}' and all related data deleted successfully",
            "server_id": server_id,
            "deleted_tokens": tokens_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to delete server: {str(e)}"
        )


@router.get("/servers/{server_id}/tokens")
async def get_server_tokens(
    server_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> List[dict]:
    """
    Retrieve all active tokens for a specific server.
    """
    # First check if the server exists
    server_statement = select(McpServer).where(
        McpServer.id == server_id,
        McpServer.is_active.is_(True),
        McpServer.user_id == current_user.id,
    )
    server = await session.execute(server_statement)
    server: McpServer = server.scalars().first()

    if not server:
        raise HTTPException(
            status_code=404, detail=f"No server found with id: {server_id}"
        )

    # Get all tokens for this server (active and inactive for management)
    token_statement = select(McpServerToken).where(
        McpServerToken.mcp_server_id == server_id
    )
    tokens = await session.execute(token_statement)
    tokens = tokens.scalars().all()

    return [
        {
            "id": token.id,
            "token": token.token,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "created_at": token.created_at.isoformat(),
            "is_active": token.is_active,
        }
        for token in tokens
    ]


@router.post("/servers/{server_id}/tokens")
async def create_server_token(
    server_id: str,
    token_data: dict = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> dict:
    """
    Create a new token for a specific server.
    """
    try:
        # Check if server exists and user has access
        server_statement = select(McpServer).where(
            McpServer.id == server_id,
            McpServer.is_active.is_(True),
            McpServer.user_id == current_user.id,
        )
        server = await session.execute(server_statement)
        server: McpServer = server.scalars().first()

        if not server:
            raise HTTPException(
                status_code=404, detail=f"No server found with id: {server_id}"
            )

        # Extract token_expires_at if provided
        token_expires_at = None
        if token_data and "expires_at" in token_data:
            token_expires_at_str = token_data.get("expires_at")
            if token_expires_at_str:
                try:
                    from dateutil import parser
                    token_expires_at = parser.parse(token_expires_at_str)
                except Exception:
                    raise HTTPException(
                        status_code=400, detail="Invalid expires_at format"
                    )

        # Generate a secure token
        token_value = f"mcp_token_{secrets.token_urlsafe(32)}"
        token = McpServerToken(
            token=token_value,
            mcp_server_id=server.id,
            user_id=current_user.id,
            expires_at=token_expires_at,
        )
        session.add(token)
        await session.commit()
        await session.refresh(token)

        return {
            "status": "created",
            "message": f"Token created successfully for server '{server.server_name}'",
            "token_id": token.id,
            "token": token_value,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "is_active": token.is_active,
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create token: {str(e)}"
        )


@router.delete("/servers/{server_id}/tokens/{token_id}")
async def delete_server_token(
    server_id: str,
    token_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> dict:
    """
    Delete a token for a specific server.
    """
    try:
        # Check if server exists and user has access
        server_statement = select(McpServer).where(
            McpServer.id == server_id,
            McpServer.is_active.is_(True),
            McpServer.user_id == current_user.id,
        )
        server = await session.execute(server_statement)
        server: McpServer = server.scalars().first()

        if not server:
            raise HTTPException(
                status_code=404, detail=f"No server found with id: {server_id}"
            )

        # Get the token
        token_statement = select(McpServerToken).where(
            McpServerToken.id == token_id,
            McpServerToken.mcp_server_id == server_id,
        )
        token = await session.execute(token_statement)
        token: McpServerToken = token.scalars().first()

        if not token:
            raise HTTPException(
                status_code=404, detail=f"No token found with id: {token_id}"
            )

        # Soft delete: mark as inactive
        token.is_active = False
        token.updated_at = datetime.utcnow()
        session.add(token)
        await session.commit()

        return {
            "status": "deleted",
            "message": "Token deleted successfully",
            "token_id": token_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to delete token: {str(e)}"
        )


@router.patch("/servers/{server_id}/tokens/{token_id}")
async def update_server_token(
    server_id: str,
    token_id: int,
    update_data: dict,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> dict:
    """
    Update a token (enable/disable or update expires_at).
    """
    try:
        # Check if server exists and user has access
        server_statement = select(McpServer).where(
            McpServer.id == server_id,
            McpServer.is_active.is_(True),
            McpServer.user_id == current_user.id,
        )
        server = await session.execute(server_statement)
        server: McpServer = server.scalars().first()

        if not server:
            raise HTTPException(
                status_code=404, detail=f"No server found with id: {server_id}"
            )

        # Get the token
        token_statement = select(McpServerToken).where(
            McpServerToken.id == token_id,
            McpServerToken.mcp_server_id == server_id,
        )
        token = await session.execute(token_statement)
        token: McpServerToken = token.scalars().first()

        if not token:
            raise HTTPException(
                status_code=404, detail=f"No token found with id: {token_id}"
            )

        # Update token fields
        if "is_active" in update_data:
            token.is_active = update_data["is_active"]

        if "expires_at" in update_data:
            expires_at_str = update_data.get("expires_at")
            if expires_at_str:
                try:
                    from dateutil import parser
                    token.expires_at = parser.parse(expires_at_str)
                except Exception:
                    raise HTTPException(
                        status_code=400, detail="Invalid expires_at format"
                    )
            else:
                token.expires_at = None

        token.updated_at = datetime.utcnow()
        session.add(token)
        await session.commit()
        await session.refresh(token)

        return {
            "status": "updated",
            "message": "Token updated successfully",
            "token_id": token.id,
            "is_active": token.is_active,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update token: {str(e)}"
        )


@router.get("/servers/{server_id}/tools/database")
async def get_database_tools(
    server_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> dict:
    """
    Retrieve tools from database with tool_type information.
    """
    # Get the server configuration
    statement = select(McpServer).where(
        McpServer.id == server_id, McpServer.is_active.is_(True)
    )
    server: McpServer = await session.execute(statement)
    server = server.scalars().first()
    if not server:
        raise HTTPException(
            status_code=404, detail=f"No server found with id: {server_id}"
        )

    # Get all tools from database (both active and inactive for management)
    server_tools: List[McpServerTool] = await session.execute(select(McpServerTool).where(McpServerTool.mcp_server_id == server_id))
    server_tools = server_tools.scalars().all()

    if not server_tools:
        return {
            "server_id": server.id,
            "server_name": server.server_name,
            "connector_id": server.connector_id,
            "tools": [],
        }

    # Transform database tools to MCP format
    tools = []
    for server_tool in server_tools:
        tool = McpServerToolItem(**server_tool.tool)
        tool_type_value = (
            server_tool.tool_type.value if server_tool.tool_type else "static"
        )
        tools.append(
            {
                "id": server_tool.id,
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema if tool.inputSchema else {},
                "tool_type": tool_type_value,  # Show tool_type
                "template_name": server_tool.template_name,
                "template_args": server_tool.template_args,
                "is_active": server_tool.is_active,
            }
        )

    return {
        "server_id": server.id,
        "server_name": server.server_name,
        "connector_id": server.connector_id,
        "tools": tools,
    }


@router.get("/servers/{server_id}/tools")
async def get_server_tools(
    server_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> dict:
    """
    Retrieve tools from database with tool_type information.
    """
    # Get the server configuration
    statement = select(McpServer).where(
        McpServer.id == server_id,
        McpServer.is_active.is_(True),
        McpServer.user_id == current_user.id,
    )
    server = await session.execute(statement)
    server: McpServer = server.scalars().first()
    if not server:
        raise HTTPException(
            status_code=404, detail=f"No server found with id: {server_id}"
        )

    # Get all tools from database (both active and inactive for management)
    server_tools: List[McpServerTool] = await session.execute(
        select(McpServerTool).where(McpServerTool.mcp_server_id == server_id))
    server_tools = server_tools.scalars().all()

    if not server_tools:
        return {
            "server_id": server.id,
            "server_name": server.server_name,
            "connector_id": server.connector_id,
            "tools": [],
        }

    # Transform database tools to MCP format
    tools = []
    for server_tool in server_tools:
        tool = McpServerToolItem(**server_tool.tool)
        tool_type_value = (
            server_tool.tool_type.value if server_tool.tool_type else "static"
        )
        tools.append(
            {
                "id": server_tool.id,
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema if tool.inputSchema else {},
                "tool_type": tool_type_value,  # Show tool_type
                "template_name": server_tool.template_name,
                "template_args": server_tool.template_args,
                "is_active": server_tool.is_active,
            }
        )

    return {
        "server_id": server.id,
        "server_name": server.server_name,
        "connector_id": server.connector_id,
        "tools": tools,
    }


@router.patch("/servers/{server_id}/tools/{tool_id}")
async def update_tool_status(
    server_id: str,
    tool_id: int,
    update_data: dict,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Update a tool's status (active/inactive).
    """
    try:
        # Verify server exists
        # Get the tool
        tool_statement = select(McpServerTool).where(
            McpServerTool.id == tool_id, McpServerTool.mcp_server_id == server_id
        )
        tool = await session.execute(tool_statement)
        tool = tool.scalars().first()
        if not tool:
            raise HTTPException(
                status_code=404,
                detail=f"No tool found with id: {tool_id} for server: {server_id}",
            )

        # Update tool status
        if "is_active" in update_data:
            tool.is_active = update_data["is_active"]
            tool.updated_at = datetime.utcnow()
            session.add(tool)
            await session.commit()
            await session.refresh(tool)

        return {
            "status": "updated",
            "message": f"Tool '{tool.name}' updated successfully",
            "tool_id": tool.id,
            "tool_name": tool.name,
            "is_active": tool.is_active,
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update tool: {str(e)}")


@router.delete("/servers/{server_id}/tools/{tool_id}")
async def delete_tool(
    server_id: str, tool_id: int, session: AsyncSession = Depends(get_async_session)
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
        tool: McpServerTool = await session.execute(
            tool_statement)
        tool: McpServerTool = tool.scalars().first()
        if not tool:
            raise HTTPException(
                status_code=404, detail=f"No tool found with id: {tool_id}"
            )

        # Check if tool is dynamic (only allow deletion of dynamic tools)
        if tool.tool_type != ToolType.dynamic:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete tool '{tool.name}'. Only dynamic tools can be deleted. This tool is of type '{tool.tool_type.value}'.",
            )

        # Permanently delete the tool from database
        tool_name = tool.name
        tool_type = tool.tool_type.value
        await session.delete(tool)
        await session.commit()

        return {
            "status": "deleted",
            "message": f"Dynamic tool '{tool_name}' permanently deleted",
            "tool_id": tool_id,
            "tool_name": tool_name,
            "tool_type": tool_type,
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete tool: {str(e)}")


@router.get("/connectors/{connector_id}/templates")
async def get_templates(
    connector_id: str, session: AsyncSession = Depends(get_async_session)
) -> List[McpConnectorTemplateItem]:
    """
    Create a new tool based on a connector template.
    """
    # Verify connector exists
    connector_statement = select(McpConnector).where(
        McpConnector.id == connector_id, McpConnector.is_active.is_(True)
    )
    connector = await session.execute(connector_statement)
    connector: McpConnector = connector.scalars().first()

    if not connector:
        raise HTTPException(
            status_code=404, detail=f"Connector with id {connector_id} not found"
        )

    # Check if template exists in connector
    templates = connector.templates_config or []
    return templates


@router.post("/servers/{server_id}/tools")
async def create_tool_from_template(
    server_id: str,
    tool_data: dict,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> McpServerToolItem:
    """
    Create a new tool based on a connector template.
    """
    tool = McpServerToolItem(**tool_data)

    # Extract template information from tool_data if present
    template_name = tool_data.get("template_name")
    template_args = tool_data.get("template_args", {})

    server_tool = McpServerTool(
        mcp_server_id=server_id,
        name=tool.name,
        template_name=template_name,
        template_args=template_args,
        tool=tool.model_dump(),
        tool_type=ToolType.dynamic.value,
        is_active=True,
    )
    print(f"Server tool: {server_tool}")
    session.add(server_tool)
    await session.commit()
    await session.refresh(server_tool)
    return server_tool.tool


# verify auth token api endpoint
@router.get("/verify-auth-token")
async def verify_auth_token(auth: McpServerToken = Depends(get_auth_token)) -> dict:
    return {"status": "verified", "message": "Auth token verified successfully"}


@app.get("/.well-known/oauth-authorization-server")
async def get_oauth_authorization_server() -> dict:
    return {
        "issuer": "https://auth.example.com",
        "authorization_endpoint": "https://auth.example.com/oauth/authorize",
        "token_endpoint": "https://auth.example.com/oauth/token",
        "userinfo_endpoint": "https://auth.example.com/oauth/userinfo",
        "jwks_uri": "https://auth.example.com/.well-known/jwks.json",
        "scopes_supported": ["openid", "profile", "email", "read", "write"],
        "response_types_supported": ["code", "token", "id_token"],
        "grant_types_supported": [
            "authorization_code",
            "client_credentials",
            "refresh_token",
        ],
        "subject_types_supported": ["public", "pairwise"],
        "id_token_signing_alg_values_supported": ["RS256", "ES256"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
        ],
        "claims_supported": ["sub", "iss", "aud", "exp", "iat", "name", "email"],
        "code_challenge_methods_supported": ["S256", "plain"],
    }


@app.get("/.well-known/oauth-protected-resource")
async def get_oauth_authorization_server() -> dict:
    return {
        "issuer": "https://auth.example.com",
        "authorization_endpoint": "https://auth.example.com/oauth/authorize",
        "token_endpoint": "https://auth.example.com/oauth/token",
        "userinfo_endpoint": "https://auth.example.com/oauth/userinfo",
        "jwks_uri": "https://auth.example.com/.well-known/jwks.json",
        "scopes_supported": ["openid", "profile", "email", "read", "write"],
        "response_types_supported": ["code", "token", "id_token"],
        "grant_types_supported": [
            "authorization_code",
            "client_credentials",
            "refresh_token",
        ],
        "subject_types_supported": ["public", "pairwise"],
        "id_token_signing_alg_values_supported": ["RS256", "ES256"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
        ],
        "claims_supported": ["sub", "iss", "aud", "exp", "iat", "name", "email"],
        "code_challenge_methods_supported": ["S256", "plain"],
    }


@router.get("/tools")
async def get_tools(
    session: AsyncSession = Depends(get_async_session),
    token: McpServerToken = Depends(get_auth_token),
) -> List[Dict[str, Any]]:
    """
    Get all tools from database.
    """
    server_tools = await session.execute(
        select(McpServerTool).where(
            McpServerTool.mcp_server_id == token.mcp_server_id,
            McpServerTool.is_active.is_(True),
        )
    )
    server_tools = server_tools.scalars().all()
    tools = []
    print(f"Server tools: {len(server_tools)}")
    print(f"Server ID: {token.mcp_server_id}")
    for server_tool in server_tools:
        tool_data = {
            "tool_type": server_tool.tool_type,
            "template_name": server_tool.template_name,
            "template_args": server_tool.template_args,
            "tool": server_tool.tool,
        }
        tools.append(tool_data)
    return tools


@router.get("/tool")
async def get_tool_by_name(
    name: str = Query(default=""),
    session: AsyncSession = Depends(get_async_session),
    token: McpServerToken = Depends(get_auth_token),
) -> Dict[str, Any]:
    """
    Get a tool by name from database.
    """
    tool = await session.execute(
        select(McpServerTool).where(
            McpServerTool.mcp_server_id == token.mcp_server_id,
            McpServerTool.is_active.is_(True),
            McpServerTool.name == name,
        )
    )
    tool = tool.scalars().first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"No tool found with name: {name}")
    tool_data = {
        "tool_type": tool.tool_type,
        "name": tool.name,
        "template_name": tool.template_name,
        "template_args": tool.template_args,
        "tool": tool.tool,
    }
    return tool_data


app.include_router(router)
