import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings

MAGIC_LINK_PURPOSE = "magic_link"
PORTAL_PURPOSE = "portal"


def create_magic_token(*, user_id: str, session_id: str, purpose: str = MAGIC_LINK_PURPOSE, hours: int = 24) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=hours)
    payload = {
        "sub": user_id,
        "session_id": session_id,
        "purpose": purpose,
        "exp": expire,
        "jti": secrets.token_hex(8),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_portal_token(*, brief_id: str, tenant_id: str = "default", days: int = 30) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=days)
    payload = {
        "brief_id": brief_id,
        "tenant_id": tenant_id,
        "purpose": PORTAL_PURPOSE,
        "exp": expire,
        "jti": secrets.token_hex(8),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, expected_purpose: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("purpose") != expected_purpose:
            return None
        return payload
    except JWTError:
        return None
