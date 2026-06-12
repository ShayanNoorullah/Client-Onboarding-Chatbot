from datetime import datetime, timezone
from typing import Any

from beanie import Document, Indexed
from pydantic import Field


class SystemConfig(Document):
    tenant_id: Indexed(str) = "default"
    product_name: str = "Client Onboarding Agent"
    support_email: str = ""
    privacy_url: str = "/privacy.html"
    phone: str = ""
    max_upload_size_mb: int = 50
    max_files_per_session: int = 20
    email_notifications_enabled: bool = True
    follow_up_enabled: bool = True
    updated_by: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "system_config"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": self.tenant_id,
            "product_name": self.product_name,
            "support_email": self.support_email,
            "privacy_url": self.privacy_url,
            "phone": self.phone,
            "max_upload_size_mb": self.max_upload_size_mb,
            "max_files_per_session": self.max_files_per_session,
            "email_notifications_enabled": self.email_notifications_enabled,
            "follow_up_enabled": self.follow_up_enabled,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat(),
        }
