from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from starlette.responses import RedirectResponse

from app.api.schemas import LoginRequest, RegisterRequest
from app.auth.dependencies import get_current_user
from app.auth.google_oauth import oauth
from app.auth.jwt import create_access_token
from app.auth.passwords import hash_password, verify_password
from app.config import settings
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
        path="/",
    )


@router.post("/register")
async def register(body: RegisterRequest, response: Response):
    email = body.email.lower()
    if await User.find_one(User.email == email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role="user",
    )
    await user.insert()
    token = create_access_token(str(user.id), user.role)
    _set_auth_cookie(response, token)
    return {"user": user.to_public(), "message": "Registration successful"}


@router.post("/login")
async def login(body: LoginRequest, response: Response):
    user = await User.find_one(User.email == body.email.lower())
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    user.last_login = datetime.now(timezone.utc)
    await user.save()
    token = create_access_token(str(user.id), user.role)
    _set_auth_cookie(response, token)
    return {"user": user.to_public(), "message": "Login successful"}


@router.get("/google/login")
async def google_login(request: Request):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if not userinfo:
        raise HTTPException(status_code=400, detail="Google auth failed")
    email = userinfo["email"].lower()
    google_id = userinfo["sub"]
    user = await User.find_one(User.email == email)
    if not user:
        user = await User.find_one(User.google_id == google_id)
    if not user:
        user = User(
            email=email,
            full_name=userinfo.get("name", email.split("@")[0]),
            google_id=google_id,
            role="user",
        )
        await user.insert()
    else:
        user.google_id = google_id
        user.last_login = datetime.now(timezone.utc)
        await user.save()
    jwt_token = create_access_token(str(user.id), user.role)
    dest = "/admin/dashboard.html" if user.role == "admin" else "/chat.html?fresh=1"
    redirect = RedirectResponse(url=f"{settings.FRONTEND_URL}{dest}")
    redirect.set_cookie(
        key=settings.COOKIE_NAME,
        value=jwt_token,
        httponly=True,
        samesite="lax",
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
        path="/",
    )
    return redirect


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(settings.COOKIE_NAME, path="/")
    return {"message": "Logged out"}


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"user": user.to_public()}
