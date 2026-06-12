import time
import uuid
from typing import Any

from app.config import settings
from app.models.ai_config import AiConfig, ModelProfile

_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = 60.0


def _default_models() -> list[ModelProfile]:
    return [
        ModelProfile(
            id="chat-default",
            name="Chat Model",
            provider="ollama",
            model_id=settings.OLLAMA_CHAT_MODEL,
            purposes=["chat"],
            temperature=float(settings.OLLAMA_CHAT_TEMPERATURE),
            is_default=True,
        ),
        ModelProfile(
            id="embed-default",
            name="Embedding Model",
            provider="ollama",
            model_id=settings.OLLAMA_EMBED_MODEL,
            purposes=["embed"],
            is_default=True,
        ),
        ModelProfile(
            id="vision-default",
            name="Vision Model",
            provider="ollama",
            model_id=settings.OLLAMA_VISION_MODEL,
            purposes=["vision"],
            is_default=True,
        ),
    ]


def _env_defaults() -> dict[str, Any]:
    models = _default_models()
    return {
        "llm_provider": settings.LLM_PROVIDER,
        "ollama_base_url": settings.OLLAMA_BASE_URL,
        "chat_temperature": settings.OLLAMA_CHAT_TEMPERATURE,
        "num_predict": 512,
        "rag_context_max_chars": settings.RAG_CONTEXT_MAX_CHARS,
        "rag_kb_chars": settings.RAG_KB_CHARS,
        "rag_client_chars": settings.RAG_CLIENT_CHARS,
        "rag_memory_chars": settings.RAG_MEMORY_CHARS,
        "rag_learned_chars": settings.RAG_LEARNED_CHARS,
        "prompt_version": settings.PROMPT_VERSION,
        "chat_model": settings.OLLAMA_CHAT_MODEL,
        "embed_model": settings.OLLAMA_EMBED_MODEL,
        "vision_model": settings.OLLAMA_VISION_MODEL,
        "models": [m.model_dump() for m in models],
    }


def invalidate_ai_cache(tenant_id: str = "default") -> None:
    _cache.pop(tenant_id, None)


async def get_ai_config_doc(tenant_id: str = "default") -> AiConfig | None:
    return await AiConfig.find_one(AiConfig.tenant_id == tenant_id)


async def get_effective_ai_settings(tenant_id: str = "default") -> dict[str, Any]:
    now = time.time()
    cached = _cache.get(tenant_id)
    if cached and now - cached[0] < _CACHE_TTL:
        return cached[1]

    merged = _env_defaults()
    doc = await get_ai_config_doc(tenant_id)
    if doc:
        merged["llm_provider"] = doc.llm_provider or merged["llm_provider"]
        merged["ollama_base_url"] = doc.ollama_base_url or merged["ollama_base_url"]
        merged["chat_temperature"] = doc.chat_temperature
        merged["num_predict"] = doc.num_predict
        merged["rag_context_max_chars"] = doc.rag_context_max_chars
        merged["rag_kb_chars"] = doc.rag_kb_chars
        merged["rag_client_chars"] = doc.rag_client_chars
        merged["rag_memory_chars"] = doc.rag_memory_chars
        merged["rag_learned_chars"] = doc.rag_learned_chars
        merged["prompt_version"] = doc.prompt_version
        if doc.models:
            merged["models"] = [m.model_dump() for m in doc.models]
            chat = doc.model_for_purpose("chat")
            embed = doc.model_for_purpose("embed")
            vision = doc.model_for_purpose("vision")
            if chat:
                merged["chat_model"] = chat.model_id
                merged["chat_temperature"] = chat.temperature
            if embed:
                merged["embed_model"] = embed.model_id
            if vision:
                merged["vision_model"] = vision.model_id

    _cache[tenant_id] = (now, merged)
    return merged


def get_effective_ai_settings_sync(tenant_id: str = "default") -> dict[str, Any]:
    now = time.time()
    cached = _cache.get(tenant_id)
    if cached and now - cached[0] < _CACHE_TTL:
        return cached[1]
    return _env_defaults()


async def warm_ai_config_cache(tenant_id: str = "default") -> dict[str, Any]:
    return await get_effective_ai_settings(tenant_id)


async def get_or_create_ai_config(tenant_id: str = "default") -> AiConfig:
    doc = await get_ai_config_doc(tenant_id)
    if doc:
        return doc
    defaults = _env_defaults()
    doc = AiConfig(
        tenant_id=tenant_id,
        llm_provider=defaults["llm_provider"],
        ollama_base_url=defaults["ollama_base_url"],
        chat_temperature=defaults["chat_temperature"],
        num_predict=defaults["num_predict"],
        rag_context_max_chars=defaults["rag_context_max_chars"],
        rag_kb_chars=defaults["rag_kb_chars"],
        rag_client_chars=defaults["rag_client_chars"],
        rag_memory_chars=defaults["rag_memory_chars"],
        rag_learned_chars=defaults["rag_learned_chars"],
        prompt_version=defaults["prompt_version"],
        models=_default_models(),
    )
    await doc.insert()
    return doc


def normalize_models(raw_models: list[dict]) -> list[ModelProfile]:
    profiles = []
    for m in raw_models:
        if not m.get("id"):
            m["id"] = str(uuid.uuid4())[:8]
        profiles.append(ModelProfile(**m))
    return profiles
