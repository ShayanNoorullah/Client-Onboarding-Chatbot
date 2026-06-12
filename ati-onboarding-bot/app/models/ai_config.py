import uuid
from datetime import datetime, timezone
from typing import Any

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class ModelProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    provider: str = "ollama"
    model_id: str
    purposes: list[str] = Field(default_factory=list)
    temperature: float = 0.3
    max_tokens: int = 512
    is_enabled: bool = True
    is_default: bool = False


class AiConfig(Document):
    tenant_id: Indexed(str) = "default"
    llm_provider: str = "ollama"
    ollama_base_url: str = ""
    chat_temperature: float = 0.3
    num_predict: int = 512
    rag_context_max_chars: int = 1500
    rag_kb_chars: int = 600
    rag_client_chars: int = 600
    rag_memory_chars: int = 300
    rag_learned_chars: int = 300
    prompt_version: str = "v2.0"
    models: list[ModelProfile] = Field(default_factory=list)
    updated_by: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "ai_config"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": self.tenant_id,
            "llm_provider": self.llm_provider,
            "ollama_base_url": self.ollama_base_url,
            "chat_temperature": self.chat_temperature,
            "num_predict": self.num_predict,
            "rag_context_max_chars": self.rag_context_max_chars,
            "rag_kb_chars": self.rag_kb_chars,
            "rag_client_chars": self.rag_client_chars,
            "rag_memory_chars": self.rag_memory_chars,
            "rag_learned_chars": self.rag_learned_chars,
            "prompt_version": self.prompt_version,
            "models": [m.model_dump() for m in self.models],
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat(),
        }

    def model_for_purpose(self, purpose: str) -> ModelProfile | None:
        defaults = [m for m in self.models if m.is_enabled and purpose in m.purposes and m.is_default]
        if defaults:
            return defaults[0]
        enabled = [m for m in self.models if m.is_enabled and purpose in m.purposes]
        return enabled[0] if enabled else None
