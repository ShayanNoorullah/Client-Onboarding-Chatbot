import re
import shutil
from pathlib import Path

from app.config import settings


def sanitise_name(raw: str) -> str:
    """Remove special chars, replace spaces with underscores, limit to 64 chars."""
    name = re.sub(r"[^\w\s-]", "", raw.strip())
    return re.sub(r"[\s]+", "_", name)[:64]


def create_client_workspace(raw_name: str) -> Path:
    """Create client folder tree. Idempotent — safe to call multiple times."""
    folder = Path(settings.STORAGE_ROOT) / sanitise_name(raw_name)
    (folder / "assets").mkdir(parents=True, exist_ok=True)
    (folder / "vectors").mkdir(parents=True, exist_ok=True)
    return folder


def save_asset(client_folder: Path, filename: str, data: bytes) -> Path:
    """Save uploaded file bytes to the client's assets/ folder."""
    safe_name = Path(filename).name
    dest = client_folder / "assets" / safe_name
    dest.write_bytes(data)
    return dest


def list_assets(client_folder: Path) -> list[str]:
    assets_dir = client_folder / "assets"
    if not assets_dir.exists():
        return []
    return [f.name for f in assets_dir.iterdir() if f.is_file()]


def delete_client_data(client_name: str) -> bool:
    """Remove entire client folder tree."""
    folder = settings.client_folder(client_name)
    if folder.exists():
        shutil.rmtree(folder)
        return True
    return False


def get_summary_path(client_name: str) -> Path:
    return settings.client_folder(client_name) / "summary.md"


def get_conversation_log_path(client_folder: Path) -> Path:
    return client_folder / "conversation_log.json"
