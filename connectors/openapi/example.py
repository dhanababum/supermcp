"""JWT-protected FastAPI server for OpenAPI connector testing.

Run:
    uv run uvicorn example:app --port 9040 --reload

Get a token:
    curl -X POST http://localhost:9040/auth/token \
      -H 'Content-Type: application/json' \
      -d '{"username":"alice","password":"wonderland"}'
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, List

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field


JWT_SECRET = "dev-secret-change-me"
JWT_ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = 60 * 60

app = FastAPI(
    title="JWT Protected Demo API",
    version="1.0.0",
    description="A small protected API for testing the OpenAPI connector.",
)
bearer_scheme = HTTPBearer()

USERS = {
    "alice": {
        "password": "wonderland",
        "id": "usr_001",
        "role": "admin",
        "team": "platform",
    },
    "bob": {
        "password": "builder",
        "id": "usr_002",
        "role": "analyst",
        "team": "growth",
    },
}

ITEMS: Dict[str, Dict[str, Any]] = {
    "item_001": {
        "id": "item_001",
        "name": "Latency dashboard",
        "status": "active",
        "owner": "alice",
    },
    "item_002": {
        "id": "item_002",
        "name": "Forecast pipeline",
        "status": "paused",
        "owner": "bob",
    },
}


class LoginRequest(BaseModel):
    username: str = Field(examples=["alice"])
    password: str = Field(examples=["wonderland"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ItemCreate(BaseModel):
    name: str
    status: str = "active"


class ItemUpdate(BaseModel):
    name: str | None = None
    status: str | None = None


class AnalysisRequest(BaseModel):
    topic: str
    limit: int = Field(default=3, ge=1, le=10)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(message: str) -> str:
    digest = hmac.new(
        JWT_SECRET.encode("utf-8"),
        message.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(digest)


def create_jwt(username: str) -> str:
    now = int(time.time())
    user = USERS[username]
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": username,
        "user_id": user["id"],
        "role": user["role"],
        "team": user["team"],
        "iat": now,
        "exp": now + TOKEN_TTL_SECONDS,
    }
    signing_input = ".".join(
        [
            _b64url_encode(json.dumps(header, separators=(",", ":")).encode()),
            _b64url_encode(json.dumps(payload, separators=(",", ":")).encode()),
        ]
    )
    return f"{signing_input}.{_sign(signing_input)}"


def verify_jwt(token: str) -> Dict[str, Any]:
    try:
        header_b64, payload_b64, signature = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}"
        expected_signature = _sign(signing_input)
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid signature")

        header = json.loads(_b64url_decode(header_b64))
        payload = json.loads(_b64url_decode(payload_b64))
        if header.get("alg") != JWT_ALGORITHM:
            raise ValueError("Unsupported algorithm")
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("Token expired")
        if payload.get("sub") not in USERS:
            raise ValueError("Unknown subject")
        return payload
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Dict[str, Any]:
    claims = verify_jwt(credentials.credentials)
    user = USERS[claims["sub"]].copy()
    user["username"] = claims["sub"]
    user["claims"] = claims
    return user


@app.post("/auth/token", response_model=TokenResponse, tags=["auth"])
async def login(payload: LoginRequest) -> TokenResponse:
    user = USERS.get(payload.username)
    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(
        access_token=create_jwt(payload.username),
        expires_in=TOKEN_TTL_SECONDS,
    )


@app.get("/me", tags=["users"])
async def get_me(user: Dict[str, Any] = Depends(current_user)) -> Dict[str, Any]:
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "team": user["team"],
    }


@app.get("/items", tags=["items"])
async def list_items(
    status_filter: str | None = Query(default=None, alias="status"),
    user: Dict[str, Any] = Depends(current_user),
) -> List[Dict[str, Any]]:
    items = list(ITEMS.values())
    if status_filter:
        items = [item for item in items if item["status"] == status_filter]
    if user["role"] != "admin":
        items = [item for item in items if item["owner"] == user["username"]]
    return items


@app.get("/items/{item_id}", tags=["items"])
async def get_item(
    item_id: str,
    user: Dict[str, Any] = Depends(current_user),
) -> Dict[str, Any]:
    item = ITEMS.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if user["role"] != "admin" and item["owner"] != user["username"]:
        raise HTTPException(status_code=403, detail="Not allowed")
    return item


@app.post("/items", tags=["items"])
async def create_item(
    payload: ItemCreate,
    user: Dict[str, Any] = Depends(current_user),
) -> Dict[str, Any]:
    item_id = f"item_{len(ITEMS) + 1:03d}"
    item = {
        "id": item_id,
        "name": payload.name,
        "status": payload.status,
        "owner": user["username"],
    }
    ITEMS[item_id] = item
    return item


@app.patch("/items/{item_id}", tags=["items"])
async def update_item(
    item_id: str,
    payload: ItemUpdate,
    user: Dict[str, Any] = Depends(current_user),
) -> Dict[str, Any]:
    item = await get_item(item_id, user)
    updates = payload.model_dump(exclude_none=True)
    item.update(updates)
    return item


@app.delete("/items/{item_id}", tags=["items"])
async def delete_item(
    item_id: str,
    user: Dict[str, Any] = Depends(current_user),
) -> Dict[str, Any]:
    item = await get_item(item_id, user)
    del ITEMS[item["id"]]
    return {"deleted": item["id"]}


@app.post("/analysis/run", tags=["analysis"])
async def run_analysis(
    payload: AnalysisRequest,
    user: Dict[str, Any] = Depends(current_user),
) -> Dict[str, Any]:
    return {
        "requested_by": user["username"],
        "topic": payload.topic,
        "limit": payload.limit,
        "results": [
            {
                "rank": index + 1,
                "summary": f"{payload.topic} signal {index + 1}",
                "score": round(0.92 - index * 0.07, 2),
            }
            for index in range(payload.limit)
        ],
    }
