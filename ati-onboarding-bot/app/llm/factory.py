import base64
import logging
from pathlib import Path

import httpx
import ollama
from langchain_ollama import ChatOllama, OllamaEmbeddings

from app.config import settings

logger = logging.getLogger(__name__)


def get_chat_llm(*, temperature: float | None = None) -> ChatOllama:
    return ChatOllama(
        model=settings.OLLAMA_CHAT_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=temperature if temperature is not None else settings.OLLAMA_CHAT_TEMPERATURE,
        num_predict=512,
    )


def get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=settings.OLLAMA_EMBED_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
    )


def describe_image_ollama(image_path: str) -> str:
    """Describe an image using Ollama vision model (llava)."""
    path = Path(image_path)
    image_bytes = path.read_bytes()
    b64 = base64.b64encode(image_bytes).decode()

    client = ollama.Client(host=settings.OLLAMA_BASE_URL)
    response = client.chat(
        model=settings.OLLAMA_VISION_MODEL,
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


def check_ollama_health() -> dict:
    """Check Ollama server and required models."""
    result = {
        "ollama_reachable": False,
        "models": [],
        "required": [
            settings.OLLAMA_CHAT_MODEL,
            settings.OLLAMA_EMBED_MODEL,
            settings.OLLAMA_VISION_MODEL,
        ],
        "missing": [],
    }
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            result["ollama_reachable"] = True
            result["models"] = [m["name"].split(":")[0] for m in data.get("models", [])]
            for req in result["required"]:
                base = req.split(":")[0]
                if not any(m.startswith(base) for m in result["models"]):
                    result["missing"].append(req)
    except Exception as e:
        logger.warning("Ollama health check failed: %s", e)
        result["missing"] = result["required"]
    return result


def stream_chat_llm(messages, *, temperature: float | None = None):
    """Yield text chunks from Ollama streaming chat."""
    llm = get_chat_llm(temperature=temperature)
    for chunk in llm.stream(messages):
        content = chunk.content
        if isinstance(content, list):
            content = "".join(str(c) for c in content)
        if content:
            yield str(content)
