from fastapi import Request

from app.models.user import User

DEFAULT_TENANT_ID = "default"


def get_request_tenant_id(request: Request) -> str:
    return getattr(request.state, "tenant_id", DEFAULT_TENANT_ID)


def get_user_tenant_id(user: User, request: Request | None = None) -> str:
    if user.is_super_admin and request:
        header = request.headers.get("X-Tenant-ID")
        if header:
            return header
    return user.tenant_id or DEFAULT_TENANT_ID
