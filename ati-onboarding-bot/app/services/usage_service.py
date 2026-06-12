from datetime import datetime, timezone

from app.models.onboarding_session import OnboardingSessionDoc
from app.models.tenant import Tenant
from app.models.usage_record import UsageRecord
from app.models.user import User


def _current_period() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year}-{now.month:02d}"


async def get_or_create_usage(tenant_id: str) -> UsageRecord:
    period = _current_period()
    record = await UsageRecord.find_one(
        UsageRecord.tenant_id == tenant_id,
        UsageRecord.period == period,
    )
    if record:
        return record
    record = UsageRecord(tenant_id=tenant_id, period=period)
    await record.insert()
    return record


async def refresh_usage_counts(tenant_id: str) -> UsageRecord:
    record = await get_or_create_usage(tenant_id)
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    record.sessions_count = await OnboardingSessionDoc.find(
        OnboardingSessionDoc.tenant_id == tenant_id,
        OnboardingSessionDoc.created_at >= month_start,
    ).count()
    record.users_count = await User.find(
        User.tenant_id == tenant_id,
        User.is_active == True,
    ).count()
    record.updated_at = datetime.now(timezone.utc)
    await record.save()
    return record


async def check_plan_limit(tenant_id: str, resource: str) -> tuple[bool, str]:
    tenant = await Tenant.find_one(Tenant.slug == tenant_id)
    if not tenant:
        return True, ""
    limits = tenant.limits or {}
    usage = await refresh_usage_counts(tenant_id)
    if resource == "sessions":
        max_sessions = limits.get("max_sessions_per_month", 500)
        if usage.sessions_count >= max_sessions:
            return False, f"Monthly session limit ({max_sessions}) reached"
    if resource == "users":
        max_users = limits.get("max_users", 50)
        if usage.users_count >= max_users:
            return False, f"User limit ({max_users}) reached"
    return True, ""
