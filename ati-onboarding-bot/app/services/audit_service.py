from fastapi import Request

from app.models.audit_event import AuditEvent


async def log_audit(
    *,
    tenant_id: str,
    actor_email: str,
    action: str,
    resource: str,
    details: dict | None = None,
    request: Request | None = None,
) -> None:
    ip = None
    if request:
        ip = request.client.host if request.client else None
    await AuditEvent(
        tenant_id=tenant_id,
        actor_email=actor_email,
        action=action,
        resource=resource,
        details=details or {},
        ip_address=ip,
    ).insert()
