import logging
import re
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.models.email_template import EmailTemplate
from app.models.smtp_config import SmtpConfig
from app.services.system_config_service import get_effective_settings
from app.storage.encryptor import decrypt_text

logger = logging.getLogger(__name__)

_VAR_RE = re.compile(r"\{\{(\w+)\}\}")


def render_template(text: str, variables: dict[str, str]) -> str:
    def repl(match: re.Match) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    return _VAR_RE.sub(repl, text)


def _normalize_emails(emails: str | list[str] | None) -> list[str]:
    if not emails:
        return []
    if isinstance(emails, str):
        emails = [emails]
    return [e.strip() for e in emails if e and e.strip()]


async def get_template(tenant_id: str, key: str) -> EmailTemplate | None:
    return await EmailTemplate.find_one(
        EmailTemplate.tenant_id == tenant_id,
        EmailTemplate.key == key,
        EmailTemplate.is_active == True,
    )


async def _get_smtp(tenant_id: str) -> tuple[SmtpConfig | None, str | None]:
    smtp = await SmtpConfig.find_one(SmtpConfig.tenant_id == tenant_id)
    if not smtp or not smtp.smtp_host or not smtp.password:
        return None, "SMTP not configured"
    try:
        password = decrypt_text(smtp.password)
    except Exception:
        return None, "Failed to decrypt SMTP password"
    return smtp, password


def _send_raw_email(
    smtp: SmtpConfig,
    password: str,
    *,
    to_emails: list[str],
    subject: str,
    body_text: str,
    body_html: str = "",
    cc_emails: list[str] | None = None,
    bcc_emails: list[str] | None = None,
) -> tuple[bool, str]:
    if not to_emails:
        return False, "No recipients"

    cc_emails = cc_emails or []
    bcc_emails = bcc_emails or []
    all_recipients = list(dict.fromkeys(to_emails + cc_emails + bcc_emails))

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp.from_email
    msg["To"] = ", ".join(to_emails)
    if cc_emails:
        msg["Cc"] = ", ".join(cc_emails)
    msg.attach(MIMEText(body_text, "plain"))
    if body_html:
        msg.attach(MIMEText(body_html, "html"))

    try:
        if smtp.encryption_protocol == "SSL":
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp.smtp_host, smtp.smtp_port, context=context) as server:
                server.login(smtp.username, password)
                server.sendmail(smtp.from_email, all_recipients, msg.as_string())
        else:
            with smtplib.SMTP(smtp.smtp_host, smtp.smtp_port, timeout=30) as server:
                if smtp.encryption_protocol == "STARTTLS":
                    server.starttls(context=ssl.create_default_context())
                if smtp.username:
                    server.login(smtp.username, password)
                server.sendmail(smtp.from_email, all_recipients, msg.as_string())
        return True, f"Email sent to {', '.join(to_emails)}"
    except Exception as e:
        logger.exception("Failed to send email")
        return False, str(e)


async def send_templated_email(
    *,
    tenant_id: str,
    template_key: str,
    to_email: str | list[str],
    variables: dict[str, str],
    cc_emails: list[str] | None = None,
    bcc_emails: list[str] | None = None,
) -> tuple[bool, str]:
    cfg = await get_effective_settings(tenant_id)
    if not cfg.get("email_notifications_enabled", True):
        return False, "Email notifications disabled"

    smtp, password_or_err = await _get_smtp(tenant_id)
    if not smtp:
        return False, password_or_err or "SMTP not configured"

    template = await get_template(tenant_id, template_key)
    if not template:
        return False, f"Template '{template_key}' not found"

    to_list = _normalize_emails(to_email)
    if not to_list:
        return False, "No recipients"

    subject = render_template(template.subject, variables)
    body_html = render_template(template.body_html, variables)
    body_text = render_template(template.body_text or template.body_html, variables)

    return _send_raw_email(
        smtp,
        password_or_err,
        to_emails=to_list,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        cc_emails=_normalize_emails(cc_emails),
        bcc_emails=_normalize_emails(bcc_emails),
    )


async def send_management_notification(
    *,
    tenant_id: str,
    template_key: str,
    variables: dict[str, str],
) -> tuple[bool, str]:
    """Send templated email to management recipients from system config."""
    cfg = await get_effective_settings(tenant_id)
    to_emails = _normalize_emails(cfg.get("notification_to_emails"))
    if not to_emails:
        return False, "No management notification recipients configured"
    cc_emails = _normalize_emails(cfg.get("notification_cc_emails"))
    return await send_templated_email(
        tenant_id=tenant_id,
        template_key=template_key,
        to_email=to_emails,
        variables=variables,
        cc_emails=cc_emails,
    )
