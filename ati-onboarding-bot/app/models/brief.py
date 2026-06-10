from datetime import datetime, timezone

from beanie import Document, Indexed
from pydantic import Field


class Brief(Document):
    user_id: Indexed(str)
    session_id: Indexed(str)
    ref_id: Indexed(str)
    client_name: str
    markdown: str
    recommended_services: list[str] = Field(default_factory=list)
    file_path: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "briefs"

    def to_public(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ref_id": self.ref_id,
            "client_name": self.client_name,
            "recommended_services": self.recommended_services,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat(),
            "download_url": f"/api/briefs/{self.id}/download",
        }
