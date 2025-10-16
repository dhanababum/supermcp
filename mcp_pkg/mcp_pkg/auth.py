from fastmcp.server.auth import TokenVerifier, AccessToken
import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .config import settings

token_header = HTTPBearer()

class CustomTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.app_base_url + "/api/verify-auth-token",
                headers={"Authorization": f"Bearer {token}"})
            if response.status_code != 200:
                return None
        return AccessToken(
            token=token,
            client_id="dummy",
            scopes=["read", "write", "admin"]
        )


def verify_token(
    token: HTTPAuthorizationCredentials = Depends(token_header)
):
    with httpx.Client(timeout=20) as client:
        response = client.get(
            settings.app_base_url + "/api/quick-token-verify",
            headers={"Authorization": f"Bearer {token.credentials}"})
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return response.json()
