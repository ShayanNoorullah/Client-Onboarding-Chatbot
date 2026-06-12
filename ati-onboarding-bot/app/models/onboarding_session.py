from datetime import datetime, timezone
from typing import Any

from beanie import Document, Indexed
from pydantic import Field

from app.storage.session_display import display_name_for_session


class OnboardingSessionDoc(Document):
    tenant_id: str = "default"
    user_id: Indexed(str)
    session_id: Indexed(str, unique=True)
    stage: str = "greeting"
    state: dict[str, Any] = Field(default_factory=dict)
    consent_given: bool = False
    project_type: str | None = None
    done: bool = False
    ref_id: str | None = None
    title: str | None = None
    pinned: bool = False
    pinned_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "onboarding_sessions"

    def to_summary(self) -> dict:
        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "user_id": self.user_id,
            "stage": self.stage,
            "consent_given": self.consent_given,
            "project_type": self.project_type,
            "done": self.done,
            "ref_id": self.ref_id,
            "title": self.title,
            "pinned": self.pinned,
            "pinned_at": self.pinned_at.isoformat() if self.pinned_at else None,
            "display_name": display_name_for_session(
                title=self.title,
                project_type=self.project_type,
                stage=self.stage,
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
