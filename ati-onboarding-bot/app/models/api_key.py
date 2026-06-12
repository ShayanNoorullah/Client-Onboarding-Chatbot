import secrets
from datetime import datetime, timezone
from typing import Any

from beanie import Document, Indexed
from pydantic import Field


class ApiKey(Document):
    tenant_id: Indexed(str)
    name: str
    key_prefix: str
    key_hash: str
    is_active: bool = True
    scopes: list[str] = Field(default_factory=lambda: ["read:sessions", "read:briefs"])
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: datetime | None = None

    class Settings:
        name = "api_keys"

    @staticmethod
    def generate_key() -> tuple[str, str]:
        raw = f"coa_{secrets.token_urlsafe(32)}"
        return raw, raw[:12]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": self.tenant_id,
            "name": self.name,
            "key_prefix": self.key_prefix,
            "is_active": self.is_active,
            "scopes": self.scopes,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }
