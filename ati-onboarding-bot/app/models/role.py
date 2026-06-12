from datetime import datetime, timezone
from typing import Any

from beanie import Document, Indexed
from pydantic import Field

PermissionsMap = dict[str, dict[str, dict[str, bool]]]


class Role(Document):
    name: Indexed(str, unique=True)
    description: str = ""
    sort_order: int = 99
    is_active: bool = True
    permissions: PermissionsMap = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "roles"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
            "permissions": self.permissions,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
