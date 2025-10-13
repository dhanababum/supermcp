from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette import status
from constants import tokens


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Apply logic only to a specific path
        if request.url.path in ["/mcp/test-1"]:
            print("Request URL: called................")
            # Get the Authorization header
            auth_header = request.headers.get("Authorization")
            
            # Check for a valid token
            if auth_header.replace("Bearer ", "") not in tokens:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Unauthorized access"}
                )
        
        # Proceed with the request
        response = await call_next(request)
        return response
