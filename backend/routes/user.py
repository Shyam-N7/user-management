from fastapi import Request, APIRouter
from fastapi.responses import JSONResponse
from auth import get_current_user
from redis_connxn import r

user_router = APIRouter()

@user_router.post('/logout')
async def logout(request: Request):
    token = request.cookies.get("token")
    if token:
        r.set(f"bl:{token}", "blacklisted", ex=3600)
    
    response = JSONResponse(content={"message": "Logout successful"}, status_code=200)
    response.delete_cookie("token")
    response.delete_cookie("user")
    response.delete_cookie("_xsrf")
    return response

@user_router.get('/me')
async def current_user(request: Request):
    user = get_current_user(request)
    return {"user": user}