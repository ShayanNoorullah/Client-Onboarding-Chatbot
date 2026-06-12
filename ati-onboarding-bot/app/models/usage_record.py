from datetime import datetime, timezone
from typing import Any

from beanie import Document, Indexed
from pydantic import Field


class UsageRecord(Document):
    tenant_id: Indexed(str)
    period: str
    sessions_count: int = 0
    users_count: int = 0
    storage_bytes: int = 0
    llm_requests: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "usage_records"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": self.tenant_id,
            "period": self.period,
            "sessions_count": self.sessions_count,
            "users_count": self.users_count,
            "storage_bytes": self.storage_bytes,
            "llm_requests": self.llm_requests,
            "updated_at": self.updated_at.isoformat(),
        }
