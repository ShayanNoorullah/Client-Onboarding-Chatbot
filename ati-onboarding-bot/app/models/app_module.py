from datetime import datetime, timezone
from typing import Any

from beanie import Document, Indexed
from pydantic import Field


class ApplicationModule(Document):
    name: Indexed(str, unique=True)
    icon: str = "fa fa-th-large"
    sort_order: int = 0
    is_active: bool = True
    created_by: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "app_modules"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "icon": self.icon,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
