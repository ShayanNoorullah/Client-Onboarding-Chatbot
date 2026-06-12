from datetime import datetime, timezone
from typing import Any, Literal

from beanie import Document, Indexed
from pydantic import Field


class FollowUpRule(Document):
    tenant_id: Indexed(str) = "default"
    trigger: Literal["session_idle", "stage_stuck", "brief_complete"] = "session_idle"
    stage: str | None = None
    delay_hours: int = 24
    template_key: str = "session_reminder"
    is_active: bool = True
    max_sends: int = 3
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "follow_up_rules"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": self.tenant_id,
            "trigger": self.trigger,
            "stage": self.stage,
            "delay_hours": self.delay_hours,
            "template_key": self.template_key,
            "is_active": self.is_active,
            "max_sends": self.max_sends,
            "updated_at": self.updated_at.isoformat(),
        }
