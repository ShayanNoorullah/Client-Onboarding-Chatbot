from datetime import datetime, timezone
from typing import Any

from beanie import Document
from pydantic import Field


class ApplicationPage(Document):
    module_name: str
    page_name: str
    route: str
    sort_order: int = 0
    is_active: bool = True
    created_by: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "app_pages"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "module_name": self.module_name,
            "page_name": self.page_name,
            "route": self.route,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
