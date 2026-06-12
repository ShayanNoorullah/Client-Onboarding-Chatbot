from app.models.system_config import SystemConfig
from app.services.system_config_service import _env_defaults, get_effective_settings_sync, invalidate_cache


def test_env_defaults_has_branding_fields():
    defaults = _env_defaults()
    assert "product_name" in defaults
    assert defaults["product_name"] == "Client Onboarding Agent"
    assert "max_upload_size_mb" in defaults


def test_system_config_to_dict():
    cfg = SystemConfig.model_construct(
        tenant_id="default",
        product_name="Test Product",
        support_email="support@example.com",
    )
    data = cfg.to_dict()
    assert data["tenant_id"] == "default"
    assert data["product_name"] == "Test Product"
    assert "chat_model" not in data


def test_effective_settings_sync_fallback():
    invalidate_cache("default")
    settings = get_effective_settings_sync("default")
    assert settings["product_name"] == "Client Onboarding Agent"
