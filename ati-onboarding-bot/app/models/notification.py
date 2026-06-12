from datetime import datetime, timezone
from typing import Any

from beanie import Document, Indexed
from pydantic import Field


class Notification(Document):
    tenant_id: Indexed(str) = "default"
    user_id: Indexed(str)
    title: str
    body: str = ""
    link: str = ""
    event_type: str = ""
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "notifications"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "title": self.title,
            "body": self.body,
            "link": self.link,
            "event_type": self.event_type,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
        }
