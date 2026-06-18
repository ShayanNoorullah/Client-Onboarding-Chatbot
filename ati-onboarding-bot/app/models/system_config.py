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
    surf_enabled: bool = True
    max_urls_per_session: int = 5
    email_notifications_enabled: bool = True
    follow_up_enabled: bool = True
    notification_to_emails: list[str] = Field(default_factory=list)
    notification_cc_emails: list[str] = Field(default_factory=list)
    slack_webhook_url: str = ""
    teams_webhook_url: str = ""
    docuseal_api_url: str = ""
    docuseal_api_key: str = ""
    docuseal_nda_template_id: str = ""
    default_language: str = "en"
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
            "surf_enabled": self.surf_enabled,
            "max_urls_per_session": self.max_urls_per_session,
            "email_notifications_enabled": self.email_notifications_enabled,
            "follow_up_enabled": self.follow_up_enabled,
            "notification_to_emails": self.notification_to_emails,
            "notification_cc_emails": self.notification_cc_emails,
            "slack_webhook_url": self.slack_webhook_url,
            "teams_webhook_url": self.teams_webhook_url,
            "docuseal_api_url": self.docuseal_api_url,
            "docuseal_api_key": "••••••••" if self.docuseal_api_key else "",
            "docuseal_nda_template_id": self.docuseal_nda_template_id,
            "default_language": self.default_language,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat(),
        }
