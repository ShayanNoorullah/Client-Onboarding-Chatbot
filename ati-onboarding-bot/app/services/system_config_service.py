import time
from typing import Any

from app.config import settings
from app.models.system_config import SystemConfig

_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = 60.0


def _env_defaults() -> dict[str, Any]:
    return {
        "product_name": "Client Onboarding Agent",
        "support_email": settings.ATI_SUPPORT_EMAIL,
        "privacy_url": settings.ATI_PRIVACY_URL,
        "phone": settings.ATI_PHONE,
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
        "max_files_per_session": settings.MAX_FILES_PER_SESSION,
        "surf_enabled": True,
        "max_urls_per_session": 5,
        "email_notifications_enabled": True,
        "follow_up_enabled": True,
        "notification_to_emails": [],
        "notification_cc_emails": [],
        "slack_webhook_url": "",
        "teams_webhook_url": "",
        "docuseal_api_url": "",
        "docuseal_api_key": "",
        "docuseal_nda_template_id": "",
        "default_language": "en",
    }


def invalidate_cache(tenant_id: str = "default") -> None:
    _cache.pop(tenant_id, None)


async def get_system_config_doc(tenant_id: str = "default") -> SystemConfig | None:
    return await SystemConfig.find_one(SystemConfig.tenant_id == tenant_id)


async def get_effective_settings(tenant_id: str = "default") -> dict[str, Any]:
    now = time.time()
    cached = _cache.get(tenant_id)
    if cached and now - cached[0] < _CACHE_TTL:
        return cached[1]

    merged = _env_defaults()
    doc = await get_system_config_doc(tenant_id)
    if doc:
        for field in merged:
            val = getattr(doc, field, None)
            if val is None:
                continue
            if isinstance(val, list):
                merged[field] = val
            elif val != "":
                merged[field] = val

    _cache[tenant_id] = (now, merged)
    return merged


def get_effective_settings_sync(tenant_id: str = "default") -> dict[str, Any]:
    now = time.time()
    cached = _cache.get(tenant_id)
    if cached and now - cached[0] < _CACHE_TTL:
        return cached[1]
    return _env_defaults()


async def warm_config_cache(tenant_id: str = "default") -> dict[str, Any]:
    return await get_effective_settings(tenant_id)


async def get_or_create_system_config(tenant_id: str = "default") -> SystemConfig:
    doc = await get_system_config_doc(tenant_id)
    if doc:
        return doc
    defaults = _env_defaults()
    doc = SystemConfig(tenant_id=tenant_id, **defaults)
    await doc.insert()
    return doc
