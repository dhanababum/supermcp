from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette import status
from constants import tokens


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/mcp/test-1"]:
            auth_header = request.headers.get("Authorization")            
            if auth_header.replace("Bearer ", "") not in tokens:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Unauthorized access"}
                )
        response = await call_next(request)
        return response
