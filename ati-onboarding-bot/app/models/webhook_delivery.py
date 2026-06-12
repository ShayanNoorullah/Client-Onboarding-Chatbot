from datetime import datetime, timezone
from typing import Any

from beanie import Document
from pydantic import Field


class WebhookDelivery(Document):
    tenant_id: str = "default"
    subscription_id: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"
    attempts: int = 0
    last_error: str = ""
    response_status: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    delivered_at: datetime | None = None

    class Settings:
        name = "webhook_deliveries"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": self.tenant_id,
            "subscription_id": self.subscription_id,
            "event_type": self.event_type,
            "status": self.status,
            "attempts": self.attempts,
            "last_error": self.last_error,
            "response_status": self.response_status,
            "created_at": self.created_at.isoformat(),
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
        }
