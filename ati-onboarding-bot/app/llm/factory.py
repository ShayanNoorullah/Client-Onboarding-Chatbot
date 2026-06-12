import base64
import logging
from pathlib import Path

import httpx
import ollama
from langchain_ollama import ChatOllama, OllamaEmbeddings

from app.services.ai_config_service import get_effective_ai_settings_sync

logger = logging.getLogger(__name__)


def _cfg(tenant_id: str = "default") -> dict:
    return get_effective_ai_settings_sync(tenant_id)


def get_chat_llm(*, temperature: float | None = None, tenant_id: str = "default") -> ChatOllama:
    cfg = _cfg(tenant_id)
    return ChatOllama(
        model=cfg["chat_model"],
        base_url=cfg["ollama_base_url"],
        temperature=temperature if temperature is not None else cfg["chat_temperature"],
        num_predict=cfg.get("num_predict", 512),
    )


def get_embeddings(tenant_id: str = "default") -> OllamaEmbeddings:
    cfg = _cfg(tenant_id)
    return OllamaEmbeddings(
        model=cfg["embed_model"],
        base_url=cfg["ollama_base_url"],
    )


def describe_image_ollama(image_path: str, tenant_id: str = "default") -> str:
    """Describe an image using Ollama vision model."""
    cfg = _cfg(tenant_id)
    path = Path(image_path)
    image_bytes = path.read_bytes()
    b64 = base64.b64encode(image_bytes).decode()

    client = ollama.Client(host=cfg["ollama_base_url"])
    response = client.chat(
        model=cfg["vision_model"],
        messages=[
            {
                "role": "user",
                "content": (
                    "Describe this image in detail for a client project brief. "
                    "Focus on: design style, colour palette, layout structure, "
                    "typography, and any visible text or branding."
                ),
                "images": [b64],
            }
        ],
    )
    return response["message"]["content"]


def check_ollama_health(tenant_id: str = "default") -> dict:
    """Check Ollama server and required models."""
    cfg = _cfg(tenant_id)
    required = [cfg["chat_model"], cfg["embed_model"], cfg["vision_model"]]
    result = {
        "ollama_reachable": False,
        "models": [],
        "required": required,
        "missing": [],
        "base_url": cfg["ollama_base_url"],
    }
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{cfg['ollama_base_url']}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            result["ollama_reachable"] = True
            result["models"] = [m["name"].split(":")[0] for m in data.get("models", [])]
            for req in required:
                base = req.split(":")[0]
                if not any(m.startswith(base) for m in result["models"]):
                    result["missing"].append(req)
    except Exception as e:
        logger.warning("Ollama health check failed: %s", e)
        result["missing"] = required
    return result


def stream_chat_llm(messages, *, temperature: float | None = None, tenant_id: str = "default"):
    """Yield text chunks from Ollama streaming chat."""
    llm = get_chat_llm(temperature=temperature, tenant_id=tenant_id)
    for chunk in llm.stream(messages):
        content = chunk.content
        if isinstance(content, list):
            content = "".join(str(c) for c in content)
        if content:
            yield str(content)
