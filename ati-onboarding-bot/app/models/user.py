from datetime import datetime, timezone
from typing import Any, Literal

from beanie import Document, Indexed
from pydantic import EmailStr, Field


class User(Document):
    tenant_id: str = "default"
    email: Indexed(EmailStr, unique=True)
    password_hash: str | None = None
    full_name: str
    username: str | None = None
    role: Literal["user", "admin"] = "user"
    role_name: str = "User"
    is_super_admin: bool = False
    google_id: str | None = None
    is_active: bool = True
    preferences: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: datetime | None = None
    last_active: datetime | None = None

    class Settings:
        name = "users"

    def to_public(self) -> dict:
        return {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "username": self.username,
            "role": self.role,
            "role_name": self.role_name,
            "tenant_id": self.tenant_id,
            "is_super_admin": self.is_super_admin,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "last_active": self.last_active.isoformat() if self.last_active else None,
        }
