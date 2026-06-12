from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.models.tenant import Tenant

DEFAULT_TENANT_ID = "default"


async def resolve_tenant_id(request: Request) -> str:
    header = request.headers.get("X-Tenant-ID")
    if header:
        tenant = await Tenant.find_one(Tenant.slug == header)
        if tenant and tenant.status == "active":
            return tenant.slug

    host = request.headers.get("host", "").split(":")[0]
    if host and host not in ("localhost", "127.0.0.1"):
        tenant = await Tenant.find_one(Tenant.custom_domain == host)
        if tenant and tenant.status == "active":
            return tenant.slug
        parts = host.split(".")
        if len(parts) >= 3:
            slug = parts[0]
            tenant = await Tenant.find_one(Tenant.slug == slug)
            if tenant and tenant.status == "active":
                return tenant.slug

    return DEFAULT_TENANT_ID


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.tenant_id = await resolve_tenant_id(request)
        return await call_next(request)
