import math

from fastapi import APIRouter, Depends, Query, Request

from app.auth.dependencies import require_admin
from app.auth.tenant_context import get_user_tenant_id
from app.models.audit_event import AuditEvent
from app.models.user import User

router = APIRouter(prefix="/api/admin/audit", tags=["admin-audit"])


@router.get("")
async def list_audit_events(
    request: Request,
    admin: User = Depends(require_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=200),
    search: str | None = Query(default=None, max_length=100),
):
    tenant_id = get_user_tenant_id(admin, request)
    events = await AuditEvent.find(AuditEvent.tenant_id == tenant_id).sort(
        -AuditEvent.created_at
    ).to_list()
    if search:
        needle = search.strip().lower()
        events = [
            e for e in events
            if needle in e.actor_email.lower()
            or needle in e.action.lower()
            or needle in e.resource.lower()
        ]
    total = len(events)
    pages = max(1, math.ceil(total / limit)) if limit else 1
    start = (page - 1) * limit
    page_items = events[start : start + limit]
    return {
        "events": [e.to_dict() for e in page_items],
        "total": total,
        "page": page,
        "pages": pages,
    }
