from fastmcp.server.auth import TokenVerifier, AccessToken
import httpx


class CustomTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.base_url + "/api/verify-auth-token",
                headers={"Authorization": f"Bearer {token}"})
            if response.status_code != 200:
                return None
        return AccessToken(
            token=token,
            client_id="dummy",
            scopes=["read", "write", "admin"]
        )
