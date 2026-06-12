from datetime import datetime, timezone
from typing import Any

from beanie import Document, Indexed
from pydantic import Field


class AuditEvent(Document):
    tenant_id: Indexed(str) = "default"
    actor_email: str
    action: str
    resource: str
    details: dict[str, Any] = Field(default_factory=dict)
    ip_address: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "audit_events"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": self.tenant_id,
            "actor_email": self.actor_email,
            "action": self.action,
            "resource": self.resource,
            "details": self.details,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat(),
        }
