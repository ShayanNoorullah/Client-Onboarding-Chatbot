from app.models.ai_config import AiConfig, ModelProfile
from app.services.ai_config_service import _env_defaults, get_effective_ai_settings_sync, invalidate_ai_cache


def test_ai_env_defaults():
    defaults = _env_defaults()
    assert defaults["llm_provider"] == "ollama" or defaults["llm_provider"]
    assert "chat_model" in defaults
    assert "models" in defaults
    assert len(defaults["models"]) >= 3


def test_ai_config_to_dict():
    cfg = AiConfig.model_construct(
        tenant_id="default",
        ollama_base_url="http://localhost:11434",
        models=[ModelProfile(id="x1", name="Test", model_id="qwen2.5:3b", purposes=["chat"])],
    )
    data = cfg.to_dict()
    assert data["tenant_id"] == "default"
    assert data["models"][0]["model_id"] == "qwen2.5:3b"


def test_model_for_purpose():
    cfg = AiConfig.model_construct(
        tenant_id="default",
        models=[
            ModelProfile(id="a", name="Chat", model_id="chat-model", purposes=["chat"], is_default=True),
            ModelProfile(id="b", name="Embed", model_id="embed-model", purposes=["embed"], is_default=True),
        ],
    )
    assert cfg.model_for_purpose("chat").model_id == "chat-model"
    assert cfg.model_for_purpose("embed").model_id == "embed-model"
    assert cfg.model_for_purpose("vision") is None


def test_effective_ai_settings_sync_fallback():
    invalidate_ai_cache("default")
    settings = get_effective_ai_settings_sync("default")
    assert settings["llm_provider"] == "ollama"
