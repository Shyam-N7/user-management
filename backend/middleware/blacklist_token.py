from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse
from redis_connxn import r

class TokenBlocklistMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.cookies.get("token")
        if token and r.get(f"bl:{token}") == "blacklisted":
            return JSONResponse(status_code=401, content={"detail": "Token is blacklisted"})
        return await call_next(request)