from datetime import datetime, timezone
from typing import Any

from beanie import Document, Indexed
from pydantic import Field


class EmailTemplate(Document):
    tenant_id: Indexed(str) = "default"
    key: Indexed(str)
    name: str
    subject: str
    body_html: str = ""
    body_text: str = ""
    variables: list[str] = Field(default_factory=list)
    is_active: bool = True
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "email_templates"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": self.tenant_id,
            "key": self.key,
            "name": self.name,
            "subject": self.subject,
            "body_html": self.body_html,
            "body_text": self.body_text,
            "variables": self.variables,
            "is_active": self.is_active,
            "updated_at": self.updated_at.isoformat(),
        }
