from datetime import datetime, timezone
from typing import Any, Literal

from beanie import Document, Indexed
from pydantic import Field


class Tenant(Document):
    slug: Indexed(str, unique=True)
    name: str
    plan: Literal["free", "pro", "enterprise"] = "free"
    status: Literal["active", "suspended", "trial"] = "active"
    custom_domain: str | None = None
    branding: dict[str, Any] = Field(
        default_factory=lambda: {"logo_url": "", "primary_color": "#0D0D0D"}
    )
    limits: dict[str, int] = Field(
        default_factory=lambda: {
            "max_users": 50,
            "max_sessions_per_month": 500,
            "max_storage_mb": 1024,
        }
    )
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tenants"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "slug": self.slug,
            "name": self.name,
            "plan": self.plan,
            "status": self.status,
            "custom_domain": self.custom_domain,
            "branding": self.branding,
            "limits": self.limits,
            "created_at": self.created_at.isoformat(),
        }
