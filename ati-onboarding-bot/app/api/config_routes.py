import logging
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.schemas import (
    AiConfigUpdate,
    EmailTemplateCreate,
    EmailTemplatePreview,
    EmailTemplateUpdate,
    FollowUpRuleUpdate,
    FollowUpRulesBulkUpdate,
    SmtpConfigUpdate,
    SmtpTestRequest,
    SystemConfigUpdate,
)
from app.auth.dependencies import require_admin, require_permission
from app.auth.tenant_context import get_user_tenant_id
from app.llm.factory import check_ollama_health
from app.models.email_template import EmailTemplate
from app.models.follow_up_rule import FollowUpRule
from app.models.smtp_config import SmtpConfig
from app.models.user import User
from app.services.audit_service import log_audit
from app.services.email_service import render_template
from app.services.ai_config_service import (
    get_or_create_ai_config,
    invalidate_ai_cache,
    normalize_models,
    warm_ai_config_cache,
)
from app.services.system_config_service import (
    get_or_create_system_config,
    invalidate_cache,
    warm_config_cache,
)
from app.storage.encryptor import decrypt_text, encrypt_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["admin-config"])

MASKED_PASSWORD = "••••••••"
_test_email_timestamps: dict[str, list[datetime]] = {}
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = timedelta(hours=1)


def _tenant_id(user: User, request: Request) -> str:
    return get_user_tenant_id(user, request)


def _check_rate_limit(admin_email: str) -> None:
    now = datetime.now(timezone.utc)
    timestamps = _test_email_timestamps.get(admin_email, [])
    timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(timestamps) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Rate limit exceeded: max 5 test emails per hour")
    timestamps.append(now)
    _test_email_timestamps[admin_email] = timestamps


async def _get_or_create_smtp(tenant_id: str) -> SmtpConfig:
    config = await SmtpConfig.find_one(SmtpConfig.tenant_id == tenant_id)
    if not config:
        config = SmtpConfig(tenant_id=tenant_id)
        await config.insert()
    return config


@router.get("/ai")
async def get_ai_config(
    request: Request,
    admin: User = Depends(require_permission("Configuration", "AI Configuration", "view")),
):
    tenant_id = _tenant_id(admin, request)
    doc = await get_or_create_ai_config(tenant_id)
    return {"config": doc.to_dict()}


@router.put("/ai")
async def update_ai_config(
    body: AiConfigUpdate,
    request: Request,
    admin: User = Depends(require_permission("Configuration", "AI Configuration", "update")),
):
    tenant_id = _tenant_id(admin, request)
    doc = await get_or_create_ai_config(tenant_id)
    data = body.model_dump(exclude_unset=True)
    if "models" in data and data["models"] is not None:
        raw = [m if isinstance(m, dict) else m.model_dump() for m in data.pop("models")]
        doc.models = normalize_models(raw)
    for field, value in data.items():
        setattr(doc, field, value)
    doc.updated_by = admin.email
    doc.updated_at = datetime.now(timezone.utc)
    await doc.save()
    invalidate_ai_cache(tenant_id)
    await warm_ai_config_cache(tenant_id)
    await log_audit(tenant_id=tenant_id, actor_email=admin.email, action="update", resource="ai_config", request=request)
    return {"config": doc.to_dict()}


@router.post("/ai/test-ollama")
async def test_ollama_ai(
    request: Request,
    admin: User = Depends(require_permission("Configuration", "AI Configuration", "view")),
):
    tenant_id = _tenant_id(admin, request)
    await warm_ai_config_cache(tenant_id)
    return check_ollama_health(tenant_id)


@router.get("/ai/ollama-models")
async def list_ollama_models(
    request: Request,
    admin: User = Depends(require_permission("Configuration", "AI Configuration", "view")),
):
    tenant_id = _tenant_id(admin, request)
    await warm_ai_config_cache(tenant_id)
    health = check_ollama_health(tenant_id)
    return {"models": health.get("models", []), "reachable": health.get("ollama_reachable", False)}


@router.get("/system")
async def get_system_config(
    request: Request,
    admin: User = Depends(require_permission("Configuration", "System Configuration", "view")),
):
    tenant_id = _tenant_id(admin, request)
    doc = await get_or_create_system_config(tenant_id)
    return {"config": doc.to_dict()}


@router.put("/system")
async def update_system_config(
    body: SystemConfigUpdate,
    request: Request,
    admin: User = Depends(require_permission("Configuration", "System Configuration", "update")),
):
    tenant_id = _tenant_id(admin, request)
    doc = await get_or_create_system_config(tenant_id)
    updates = body.model_dump(exclude_unset=True)
    if updates.get("docuseal_api_key") == MASKED_PASSWORD:
        updates.pop("docuseal_api_key", None)
    for field, value in updates.items():
        if field == "docuseal_api_key" and value:
            value = encrypt_text(value)
        setattr(doc, field, value)
    doc.updated_by = admin.email
    doc.updated_at = datetime.now(timezone.utc)
    await doc.save()
    invalidate_cache(tenant_id)
    await warm_config_cache(tenant_id)
    await log_audit(
        tenant_id=tenant_id,
        actor_email=admin.email,
        action="update",
        resource="system_config",
        request=request,
    )
    return {"config": doc.to_dict()}


@router.get("/smtp")
async def get_smtp_config(
    request: Request,
    admin: User = Depends(require_permission("Configuration", "SMTP", "view")),
):
    tenant_id = _tenant_id(admin, request)
    config = await SmtpConfig.find_one(SmtpConfig.tenant_id == tenant_id)
    if not config:
        return {"config": None}
    return {"config": config.to_dict(mask_password=True)}


@router.put("/smtp")
async def update_smtp_config(
    body: SmtpConfigUpdate,
    request: Request,
    admin: User = Depends(require_permission("Configuration", "SMTP", "update")),
):
    tenant_id = _tenant_id(admin, request)
    config = await _get_or_create_smtp(tenant_id)
    config.smtp_host = body.smtp_host
    config.smtp_port = body.smtp_port
    config.encryption_protocol = body.encryption_protocol
    config.from_email = body.from_email
    config.username = body.username
    if body.password and body.password != MASKED_PASSWORD:
        try:
            config.password = encrypt_text(body.password)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
    config.is_active = True
    config.updated_by = admin.email
    config.updated_at = datetime.now(timezone.utc)
    await config.save()
    await log_audit(tenant_id=tenant_id, actor_email=admin.email, action="update", resource="smtp_config", request=request)
    return {"config": config.to_dict(mask_password=True)}


@router.post("/smtp/test")
async def test_smtp_config(
    body: SmtpTestRequest,
    request: Request,
    admin: User = Depends(require_permission("Configuration", "SMTP", "update")),
):
    _check_rate_limit(admin.email)
    tenant_id = _tenant_id(admin, request)
    config = await SmtpConfig.find_one(SmtpConfig.tenant_id == tenant_id)
    if not config or not config.smtp_host:
        return {"success": False, "message": "SMTP not configured"}
    if not config.password:
        return {"success": False, "message": "SMTP password not set"}

    try:
        password = decrypt_text(config.password)
    except Exception:
        return {"success": False, "message": "Failed to decrypt SMTP password"}

    msg = MIMEText("This is a test email from Client Onboarding Agent Admin.")
    msg["Subject"] = "SMTP Test"
    msg["From"] = config.from_email
    msg["To"] = body.test_email

    try:
        if config.encryption_protocol == "SSL":
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, context=context) as server:
                server.login(config.username, password)
                server.sendmail(config.from_email, [body.test_email], msg.as_string())
        else:
            with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as server:
                if config.encryption_protocol == "STARTTLS":
                    server.starttls(context=ssl.create_default_context())
                if config.username:
                    server.login(config.username, password)
                server.sendmail(config.from_email, [body.test_email], msg.as_string())
        return {"success": True, "message": f"Test email sent to {body.test_email}"}
    except Exception as e:
        logger.exception("SMTP test failed")
        return {"success": False, "message": str(e)}


@router.get("/email-templates")
async def get_email_templates(
    request: Request,
    admin: User = Depends(require_permission("Configuration", "Email Templates", "view")),
):
    tenant_id = _tenant_id(admin, request)
    templates = await EmailTemplate.find(EmailTemplate.tenant_id == tenant_id).to_list()
    return {"templates": [t.to_dict() for t in templates]}


@router.post("/email-templates")
async def create_email_template(
    body: EmailTemplateCreate,
    request: Request,
    admin: User = Depends(require_permission("Configuration", "Email Templates", "insert")),
):
    tenant_id = _tenant_id(admin, request)
    existing = await EmailTemplate.find_one(
        EmailTemplate.tenant_id == tenant_id,
        EmailTemplate.key == body.key,
    )
    if existing:
        raise HTTPException(status_code=400, detail="Template key already exists")
    tpl = EmailTemplate(tenant_id=tenant_id, **body.model_dump())
    await tpl.insert()
    return {"template": tpl.to_dict()}


@router.put("/email-templates/{key}")
async def update_email_template(
    key: str,
    body: EmailTemplateUpdate,
    request: Request,
    admin: User = Depends(require_permission("Configuration", "Email Templates", "update")),
):
    tenant_id = _tenant_id(admin, request)
    tpl = await EmailTemplate.find_one(EmailTemplate.tenant_id == tenant_id, EmailTemplate.key == key)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(tpl, field, value)
    tpl.updated_at = datetime.now(timezone.utc)
    await tpl.save()
    return {"template": tpl.to_dict()}


@router.delete("/email-templates/{key}")
async def delete_email_template(
    key: str,
    request: Request,
    admin: User = Depends(require_permission("Configuration", "Email Templates", "delete")),
):
    tenant_id = _tenant_id(admin, request)
    tpl = await EmailTemplate.find_one(EmailTemplate.tenant_id == tenant_id, EmailTemplate.key == key)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    await tpl.delete()
    return {"status": "deleted", "key": key}


@router.post("/email-templates/{key}/preview")
async def preview_email_template(
    key: str,
    body: EmailTemplatePreview,
    request: Request,
    admin: User = Depends(require_permission("Configuration", "Email Templates", "view")),
):
    tenant_id = _tenant_id(admin, request)
    tpl = await EmailTemplate.find_one(EmailTemplate.tenant_id == tenant_id, EmailTemplate.key == key)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    vars_ = {
        "client_name": "Jane Doe",
        "product_name": "Client Onboarding Agent",
        "session_link": "https://example.com/chat.html",
        "brief_link": "https://example.com/briefs/123",
        "brief_summary": "Sample brief summary",
        "stage": "requirements",
        **body.variables,
    }
    return {
        "subject": render_template(tpl.subject, vars_),
        "body_html": render_template(tpl.body_html, vars_),
        "body_text": render_template(tpl.body_text or tpl.body_html, vars_),
    }


@router.get("/follow-up-rules")
async def get_follow_up_rules(
    request: Request,
    admin: User = Depends(require_permission("Configuration", "Follow-up Timing", "view")),
):
    tenant_id = _tenant_id(admin, request)
    rules = await FollowUpRule.find(FollowUpRule.tenant_id == tenant_id).to_list()
    return {"rules": [r.to_dict() for r in rules]}


@router.put("/follow-up-rules")
async def update_follow_up_rules(
    body: FollowUpRulesBulkUpdate,
    request: Request,
    admin: User = Depends(require_permission("Configuration", "Follow-up Timing", "update")),
):
    tenant_id = _tenant_id(admin, request)
    updated = []
    for rule_data in body.rules:
        if rule_data.id:
            rule = await FollowUpRule.get(rule_data.id)
            if not rule or rule.tenant_id != tenant_id:
                continue
        else:
            rule = FollowUpRule(tenant_id=tenant_id)
        for field, value in rule_data.model_dump(exclude_unset=True, exclude={"id"}).items():
            setattr(rule, field, value)
        rule.updated_at = datetime.now(timezone.utc)
        if rule_data.id:
            await rule.save()
        else:
            await rule.insert()
        updated.append(rule.to_dict())
    return {"rules": updated}
