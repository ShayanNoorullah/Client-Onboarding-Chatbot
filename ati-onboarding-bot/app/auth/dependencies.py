from fastapi import Cookie, Depends, HTTPException, Request, WebSocket, status

from app.auth.jwt import decode_access_token
from app.config import settings
from app.models.user import User


async def _user_from_token(token: str | None) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = await User.get(payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


async def get_current_user(
    request: Request,
    access_token: str | None = Cookie(default=None, alias=settings.COOKIE_NAME),
) -> User:
    token = access_token
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    return await _user_from_token(token)


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


async def get_ws_user(websocket: WebSocket) -> User | None:
    token = websocket.query_params.get("token") or websocket.cookies.get(settings.COOKIE_NAME)
    if not token:
        await websocket.close(code=4401)
        return None
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        await websocket.close(code=4401)
        return None
    user = await User.get(payload["sub"])
    if not user or not user.is_active:
        await websocket.close(code=4401)
        return None
    return user
