import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.schemas import WebhookSubscriptionCreate, WebhookSubscriptionUpdate
from app.auth.dependencies import require_permission
from app.auth.tenant_context import get_user_tenant_id
from app.models.user import User
from app.models.webhook_delivery import WebhookDelivery
from app.models.webhook_subscription import WebhookSubscription
from app.services.audit_service import log_audit
from app.services.webhook_dispatcher import deliver_webhook

router = APIRouter(prefix="/api/admin/webhooks", tags=["webhooks"])

MASKED = "••••••••"


def _tenant_id(user: User, request: Request) -> str:
    return get_user_tenant_id(user, request)


@router.get("")
async def list_webhooks(
    request: Request,
    admin: User = Depends(require_permission("Configuration", "Webhooks", "view")),
):
    tenant_id = _tenant_id(admin, request)
    subs = await WebhookSubscription.find(WebhookSubscription.tenant_id == tenant_id).to_list()
    return {"webhooks": [s.to_dict() for s in subs]}


@router.post("")
async def create_webhook(
    body: WebhookSubscriptionCreate,
    request: Request,
    admin: User = Depends(require_permission("Configuration", "Webhooks", "insert")),
):
    tenant_id = _tenant_id(admin, request)
    secret = body.secret or secrets.token_hex(16)
    sub = WebhookSubscription(
        tenant_id=tenant_id,
        name=body.name,
        url=body.url,
        secret=secret,
        event_types=body.event_types,
        max_retries=body.max_retries,
        created_by=admin.email,
    )
    await sub.insert()
    await log_audit(tenant_id=tenant_id, actor_email=admin.email, action="create", resource="webhook", request=request)
    return {"webhook": sub.to_dict(mask_secret=False)}


@router.put("/{webhook_id}")
async def update_webhook(
    webhook_id: str,
    body: WebhookSubscriptionUpdate,
    request: Request,
    admin: User = Depends(require_permission("Configuration", "Webhooks", "update")),
):
    tenant_id = _tenant_id(admin, request)
    sub = await WebhookSubscription.get(webhook_id)
    if not sub or sub.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Webhook not found")
    if body.name is not None:
        sub.name = body.name
    if body.url is not None:
        sub.url = body.url
    if body.event_types is not None:
        sub.event_types = body.event_types
    if body.is_active is not None:
        sub.is_active = body.is_active
    if body.max_retries is not None:
        sub.max_retries = body.max_retries
    if body.secret and body.secret != MASKED:
        sub.secret = body.secret
    sub.updated_at = datetime.now(timezone.utc)
    await sub.save()
    return {"webhook": sub.to_dict()}


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    request: Request,
    admin: User = Depends(require_permission("Configuration", "Webhooks", "delete")),
):
    tenant_id = _tenant_id(admin, request)
    sub = await WebhookSubscription.get(webhook_id)
    if not sub or sub.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await sub.delete()
    return {"message": "Deleted"}


@router.get("/deliveries")
async def list_deliveries(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    admin: User = Depends(require_permission("Configuration", "Webhooks", "view")),
):
    tenant_id = _tenant_id(admin, request)
    deliveries = await WebhookDelivery.find(
        WebhookDelivery.tenant_id == tenant_id
    ).sort(-WebhookDelivery.created_at).limit(limit).to_list()
    return {"deliveries": [d.to_dict() for d in deliveries]}


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    request: Request,
    admin: User = Depends(require_permission("Configuration", "Webhooks", "update")),
):
    tenant_id = _tenant_id(admin, request)
    sub = await WebhookSubscription.get(webhook_id)
    if not sub or sub.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Webhook not found")
    delivery = await deliver_webhook(sub, "test.ping", {"message": "Test from ATI Onboarding Agent"})
    return {"delivery": delivery.to_dict()}
