import json
import logging
from typing import Any

import httpx

from app.models.notification import Notification
from app.models.user import User
from app.services.email_service import send_management_notification, send_templated_email
from app.services.system_config_service import get_effective_settings
from app.services.webhook_dispatcher import dispatch_webhooks

logger = logging.getLogger(__name__)

EVENT_BRIEF_CREATED = "brief.created"
EVENT_BRIEF_UPDATED = "brief.updated"
EVENT_SESSION_CREATED = "session.created"
EVENT_SESSION_COMPLETED = "session.completed"
EVENT_SESSION_ABANDONED = "session.abandoned"
EVENT_USER_REGISTERED = "user.registered"


async def _notify_admins_inbox(tenant_id: str, title: str, body: str, link: str = "", event_type: str = "") -> None:
    admins = await User.find(User.tenant_id == tenant_id, User.role == "admin", User.is_active == True).to_list()
    for admin in admins:
        await Notification(
            tenant_id=tenant_id,
            user_id=str(admin.id),
            title=title,
            body=body,
            link=link,
            event_type=event_type,
        ).insert()


async def _post_chat_webhook(url: str, text: str, channel: str = "slack") -> bool:
    if not url:
        return False
    try:
        if channel == "teams":
            payload = {"@type": "MessageCard", "text": text}
        else:
            payload = {"text": text}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
        return 200 <= resp.status_code < 300
    except Exception:
        logger.exception("Chat webhook failed")
        return False


async def dispatch_event(
    tenant_id: str,
    event_type: str,
    payload: dict[str, Any],
    *,
    email_template: str | None = None,
    email_to: str | list[str] | None = None,
    email_variables: dict[str, str] | None = None,
    notify_admins: bool = False,
    admin_title: str = "",
    admin_body: str = "",
    admin_link: str = "",
) -> None:
    """Central event dispatcher: webhooks, email, chat, in-app."""
    await dispatch_webhooks(tenant_id, event_type, payload)

    cfg = await get_effective_settings(tenant_id)
    chat_text = f"[{event_type}] {json.dumps(payload, default=str)[:500]}"

    await _post_chat_webhook(cfg.get("slack_webhook_url", ""), chat_text, "slack")
    await _post_chat_webhook(cfg.get("teams_webhook_url", ""), chat_text, "teams")

    if email_template and email_to:
        await send_templated_email(
            tenant_id=tenant_id,
            template_key=email_template,
            to_email=email_to,
            variables=email_variables or {},
        )
    elif email_template and event_type == EVENT_BRIEF_CREATED:
        await send_management_notification(
            tenant_id=tenant_id,
            template_key=email_template,
            variables=email_variables or {},
        )

    if notify_admins:
        await _notify_admins_inbox(tenant_id, admin_title, admin_body, admin_link, event_type)
