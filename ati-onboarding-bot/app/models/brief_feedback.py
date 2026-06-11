from datetime import datetime, timezone

from beanie import Document, Indexed
from pydantic import Field


class BriefFeedback(Document):
    user_id: Indexed(str)
    brief_id: Indexed(str)
    session_id: str
    rating: int = Field(ge=1, le=5)
    comment: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "brief_feedback"

    def to_public(self) -> dict:
        return {
            "id": str(self.id),
            "brief_id": self.brief_id,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat(),
        }
