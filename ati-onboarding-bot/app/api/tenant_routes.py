import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.schemas import ApiKeyCreate, TenantCreate, TenantUpdate
from app.auth.dependencies import require_admin, require_super_admin
from app.auth.tenant_context import get_user_tenant_id
from app.models.api_key import ApiKey
from app.models.tenant import Tenant
from app.models.user import User
from app.db.seeders import seed_tenant_defaults
from app.services.audit_service import log_audit
from app.services.usage_service import refresh_usage_counts

router = APIRouter(prefix="/api/admin/tenants", tags=["tenants"])


@router.get("")
async def list_tenants(_: User = Depends(require_super_admin)):
    tenants = await Tenant.find_all().to_list()
    return {"tenants": [t.to_dict() for t in tenants]}


@router.post("")
async def create_tenant(
    body: TenantCreate,
    request: Request,
    admin: User = Depends(require_super_admin),
):
    if await Tenant.find_one(Tenant.slug == body.slug):
        raise HTTPException(status_code=400, detail="Tenant slug already exists")
    tenant = Tenant(slug=body.slug, name=body.name, plan=body.plan)
    await tenant.insert()
    await seed_tenant_defaults(tenant.slug)
    await log_audit(
        tenant_id=tenant.slug,
        actor_email=admin.email,
        action="create",
        resource="tenant",
        details={"slug": tenant.slug},
        request=request,
    )
    return {"tenant": tenant.to_dict()}


@router.get("/current")
async def get_current_tenant(request: Request, user: User = Depends(require_admin)):
    tenant_id = get_user_tenant_id(user, request)
    tenant = await Tenant.find_one(Tenant.slug == tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"tenant": tenant.to_dict()}


@router.patch("/current")
async def patch_current_tenant(
    body: TenantUpdate,
    request: Request,
    user: User = Depends(require_admin),
):
    tenant_id = get_user_tenant_id(user, request)
    tenant = await Tenant.find_one(Tenant.slug == tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    data = body.model_dump(exclude_unset=True)
    if "branding" in data and data["branding"]:
        tenant.branding = {**tenant.branding, **data.pop("branding")}
    if "limits" in data and data["limits"]:
        tenant.limits = {**tenant.limits, **data.pop("limits")}
    for field, value in data.items():
        setattr(tenant, field, value)
    await tenant.save()
    await log_audit(
        tenant_id=tenant_id,
        actor_email=user.email,
        action="update",
        resource="tenant",
        details={"slug": tenant.slug},
        request=request,
    )
    return {"tenant": tenant.to_dict()}


@router.get("/usage")
async def get_usage(request: Request, user: User = Depends(require_admin)):
    tenant_id = get_user_tenant_id(user, request)
    record = await refresh_usage_counts(tenant_id)
    tenant = await Tenant.find_one(Tenant.slug == tenant_id)
    return {
        "usage": record.to_dict(),
        "limits": tenant.limits if tenant else {},
        "tenant_id": tenant_id,
    }


@router.get("/api-keys")
async def list_api_keys(request: Request, user: User = Depends(require_admin)):
    tenant_id = get_user_tenant_id(user, request)
    keys = await ApiKey.find(ApiKey.tenant_id == tenant_id).to_list()
    return {"api_keys": [k.to_dict() for k in keys]}


@router.post("/api-keys")
async def create_api_key(
    body: ApiKeyCreate,
    request: Request,
    user: User = Depends(require_admin),
):
    tenant_id = get_user_tenant_id(user, request)
    raw, prefix = ApiKey.generate_key()
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    doc = ApiKey(
        tenant_id=tenant_id,
        name=body.name,
        key_prefix=prefix,
        key_hash=key_hash,
        created_by=user.email,
    )
    await doc.insert()
    await log_audit(
        tenant_id=tenant_id,
        actor_email=user.email,
        action="create",
        resource="api_key",
        details={"name": body.name},
        request=request,
    )
    result = doc.to_dict()
    result["key"] = raw
    return {"api_key": result}


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    request: Request,
    user: User = Depends(require_admin),
):
    doc = await ApiKey.get(key_id)
    if not doc:
        raise HTTPException(status_code=404, detail="API key not found")
    tenant_id = get_user_tenant_id(user, request)
    if doc.tenant_id != tenant_id and not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Cannot revoke key for another tenant")
    doc.is_active = False
    await doc.save()
    await log_audit(
        tenant_id=doc.tenant_id,
        actor_email=user.email,
        action="revoke",
        resource="api_key",
        details={"id": key_id},
        request=request,
    )
    return {"status": "revoked", "id": key_id}
