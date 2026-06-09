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

    STORAGE_ROOT: Path = Path(os.getenv("STORAGE_ROOT", "./client_data"))
    ATI_KB_ROOT: Path = Path(os.getenv("ATI_KB_ROOT", "./ati_kb"))
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    ATI_PRIVACY_URL: str = os.getenv(
        "ATI_PRIVACY_URL", "https://awesometechinc.com/privacy-policy/"
    )
    ATI_SUPPORT_EMAIL: str = os.getenv("ATI_SUPPORT_EMAIL", "support@awesometechinc.com")
    ATI_PHONE: str = os.getenv("ATI_PHONE", "877-284-4968")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_FILES_PER_SESSION: int = 20
    RAG_CONTEXT_MAX_CHARS: int = 1500

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

    def client_vectors_dir(self, client_name: str) -> Path:
        return self.client_folder(client_name) / "vectors"


settings = Settings()
