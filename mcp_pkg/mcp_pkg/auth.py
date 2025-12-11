from fastmcp.server.auth import TokenVerifier, AccessToken
import httpx
from starlette.requests import Request
from starlette.exceptions import HTTPException
from .config import settings


class CustomTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.app_base_url + "/api/verify-auth-token",
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code != 200:
                return None
        return AccessToken(
            token=token, client_id="dummy", scopes=["read", "write", "admin"]
        )


async def verify_token(request: Request):
    token = request.headers.get("Authorization").replace("Bearer ", "")
    async with httpx.AsyncClient(timeout=20) as client:
        print(
            f"Verifying token {settings.app_base_url}/api/quick-token-verify, Bearer {token}................."
        )
        response = await client.get(
            settings.app_base_url + "/api/quick-token-verify",
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")
        return response.json()
