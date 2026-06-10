from datetime import datetime, timezone
from typing import Any

from beanie import Document, Indexed
from pydantic import Field


class UserMemory(Document):
    user_id: Indexed(str, unique=True)
    facts: list[str] = Field(default_factory=list)
    project_history: list[dict[str, Any]] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "user_memories"
