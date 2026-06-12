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


async def get_template(tenant_id: str, key: str) -> EmailTemplate | None:
    return await EmailTemplate.find_one(
        EmailTemplate.tenant_id == tenant_id,
        EmailTemplate.key == key,
        EmailTemplate.is_active == True,
    )


async def send_templated_email(
    *,
    tenant_id: str,
    template_key: str,
    to_email: str,
    variables: dict[str, str],
) -> tuple[bool, str]:
    cfg = await get_effective_settings(tenant_id)
    if not cfg.get("email_notifications_enabled", True):
        return False, "Email notifications disabled"

    smtp = await SmtpConfig.find_one(SmtpConfig.tenant_id == tenant_id)
    if not smtp or not smtp.smtp_host or not smtp.password:
        return False, "SMTP not configured"

    template = await get_template(tenant_id, template_key)
    if not template:
        return False, f"Template '{template_key}' not found"

    subject = render_template(template.subject, variables)
    body_html = render_template(template.body_html, variables)
    body_text = render_template(template.body_text or template.body_html, variables)

    try:
        password = decrypt_text(smtp.password)
    except Exception:
        return False, "Failed to decrypt SMTP password"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp.from_email
    msg["To"] = to_email
    msg.attach(MIMEText(body_text, "plain"))
    if body_html:
        msg.attach(MIMEText(body_html, "html"))

    try:
        if smtp.encryption_protocol == "SSL":
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp.smtp_host, smtp.smtp_port, context=context) as server:
                server.login(smtp.username, password)
                server.sendmail(smtp.from_email, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(smtp.smtp_host, smtp.smtp_port, timeout=30) as server:
                if smtp.encryption_protocol == "STARTTLS":
                    server.starttls(context=ssl.create_default_context())
                if smtp.username:
                    server.login(smtp.username, password)
                server.sendmail(smtp.from_email, [to_email], msg.as_string())
        return True, f"Email sent to {to_email}"
    except Exception as e:
        logger.exception("Failed to send email")
        return False, str(e)
