from datetime import datetime, timezone
from typing import Any

from beanie import Document
from pydantic import Field


class ApplicationAction(Document):
    page_name: str
    action_name: str
    action_key: str
    sort_order: int = 0
    is_pinned: bool = False
    is_active: bool = True
    created_by: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "app_actions"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "page_name": self.page_name,
            "action_name": self.action_name,
            "action_key": self.action_key,
            "sort_order": self.sort_order,
            "is_pinned": self.is_pinned,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
