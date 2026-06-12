from datetime import datetime, timezone
from typing import Any

from beanie import Document, Indexed
from pydantic import Field


class WebhookSubscription(Document):
    tenant_id: Indexed(str) = "default"
    name: str
    url: str
    secret: str = ""
    event_types: list[str] = Field(default_factory=list)
    is_active: bool = True
    max_retries: int = 3
    created_by: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "webhook_subscriptions"

    def to_dict(self, mask_secret: bool = True) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": self.tenant_id,
            "name": self.name,
            "url": self.url,
            "secret": "••••••••" if mask_secret and self.secret else self.secret,
            "event_types": self.event_types,
            "is_active": self.is_active,
            "max_retries": self.max_retries,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
