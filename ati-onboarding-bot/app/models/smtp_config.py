from datetime import datetime, timezone
from typing import Any

from beanie import Document, Indexed
from pydantic import Field


class SmtpConfig(Document):
    tenant_id: Indexed(str) = "default"
    smtp_host: str = ""
    smtp_port: int = 587
    encryption_protocol: str = "STARTTLS"
    from_email: str = ""
    username: str = ""
    password: str = ""
    is_active: bool = True
    updated_by: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "smtp_config"

    def to_dict(self, mask_password: bool = True) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": self.tenant_id,
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "encryption_protocol": self.encryption_protocol,
            "from_email": self.from_email,
            "username": self.username,
            "password": "••••••••" if mask_password and self.password else self.password,
            "is_active": self.is_active,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat(),
        }
