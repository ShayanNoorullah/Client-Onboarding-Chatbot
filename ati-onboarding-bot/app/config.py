import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_CHAT_MODEL: str = os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5:3b")
    OLLAMA_EMBED_MODEL: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    OLLAMA_VISION_MODEL: str = os.getenv("OLLAMA_VISION_MODEL", "llava")
    OLLAMA_CHAT_TEMPERATURE: float = float(os.getenv("OLLAMA_CHAT_TEMPERATURE", "0.3"))

    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "ati_onboarding")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://127.0.0.1:8001/api/auth/google/callback"
    )
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://127.0.0.1:8001")

    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@awesometechinc.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "Admin123!")
    ADMIN_FULL_NAME: str = os.getenv("ADMIN_FULL_NAME", "ATI Admin")

    STORAGE_ROOT: Path = Path(os.getenv("STORAGE_ROOT", "./client_data"))
    ATI_KB_ROOT: Path = Path(os.getenv("ATI_KB_ROOT", "./ati_kb"))
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    ATI_PRIVACY_URL: str = os.getenv("ATI_PRIVACY_URL", "/privacy.html")
    ATI_SUPPORT_EMAIL: str = os.getenv("ATI_SUPPORT_EMAIL", "support@awesometechinc.com")
    ATI_PHONE: str = os.getenv("ATI_PHONE", "877-284-4968")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_FILES_PER_SESSION: int = 20
    RAG_CONTEXT_MAX_CHARS: int = 1500
    RAG_KB_CHARS: int = int(os.getenv("RAG_KB_CHARS", "600"))
    RAG_CLIENT_CHARS: int = int(os.getenv("RAG_CLIENT_CHARS", "600"))
    RAG_MEMORY_CHARS: int = int(os.getenv("RAG_MEMORY_CHARS", "300"))
    RAG_LEARNED_CHARS: int = int(os.getenv("RAG_LEARNED_CHARS", "300"))
    PROMPT_VERSION: str = os.getenv("PROMPT_VERSION", "v2.0")
    COOKIE_NAME: str = "access_token"

    SUPPORTED_EXTENSIONS: set[str] = {
        ".jpg", ".jpeg", ".png", ".gif", ".webp",
        ".pdf", ".docx", ".xlsx", ".txt", ".csv",
    }

    @property
    def ati_kb_vectors_dir(self) -> Path:
        return self.ATI_KB_ROOT / "vectors"

    def client_folder(self, client_name: str) -> Path:
        from app.storage.file_manager import sanitise_name

        return self.STORAGE_ROOT / sanitise_name(client_name)

    def project_folder(self, client_name: str, workspace_slug: str) -> Path:
        return self.client_folder(client_name) / workspace_slug

    def client_vectors_dir(self, client_name: str, workspace_slug: str | None = None) -> Path:
        if workspace_slug:
            return self.project_folder(client_name, workspace_slug) / "vectors"
        return self.client_folder(client_name) / "vectors"


settings = Settings()
