import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings

CONVERSATION_LOG_SCHEMA_VERSION = 1


def sanitise_name(raw: str) -> str:
    """Remove special chars, replace spaces with underscores, limit to 64 chars."""
    name = re.sub(r"[^\w\s-]", "", raw.strip())
    return re.sub(r"[\s]+", "_", name)[:64]


def make_workspace_slug(session_id: str) -> str:
    """Date + short session id for unique project folders."""
    date_part = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    short_id = (session_id or "unknown")[:8]
    return f"{date_part}_{short_id}"


def create_client_workspace(raw_name: str) -> Path:
    """Legacy: client root folder (creates assets/ for backward compatibility)."""
    folder = Path(settings.STORAGE_ROOT) / sanitise_name(raw_name)
    (folder / "assets").mkdir(parents=True, exist_ok=True)
    (folder / "vectors").mkdir(parents=True, exist_ok=True)
    return folder


def create_project_workspace(client_name: str, session_id: str) -> tuple[Path, str]:
    """Create dated project subfolder under client name."""
    slug = make_workspace_slug(session_id)
    folder = settings.project_folder(client_name, slug)
    (folder / "assets").mkdir(parents=True, exist_ok=True)
    (folder / "vectors").mkdir(parents=True, exist_ok=True)
    return folder, slug


def get_project_folder_from_state(state: dict[str, Any]) -> Path:
    """Resolve project folder from state; fallback to legacy flat layout."""
    client_name = state.get("client_name")
    if not client_name:
        raise ValueError("client_name required")
    slug = state.get("workspace_slug")
    if slug:
        return settings.project_folder(client_name, slug)
    folder = settings.client_folder(client_name)
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


def delete_client_data(client_name: str, workspace_slug: str | None = None) -> bool:
    """Remove client or specific project folder."""
    if workspace_slug:
        folder = settings.project_folder(client_name, workspace_slug)
    else:
        folder = settings.client_folder(client_name)
    if folder.exists():
        shutil.rmtree(folder)
        return True
    return False


def get_summary_path(client_name: str, workspace_slug: str | None = None) -> Path:
    if workspace_slug:
        return settings.project_folder(client_name, workspace_slug) / "summary.md"
    return settings.client_folder(client_name) / "summary.md"


def get_conversation_log_path(client_folder: Path) -> Path:
    return client_folder / "conversation_log.json"


def get_encrypted_log_path(client_folder: Path) -> Path:
    return client_folder / "conversation_log.enc"


def write_conversation_log(client_folder: Path, data: dict) -> Path:
    """Write structured, human-readable conversation log JSON."""
    log_path = get_conversation_log_path(client_folder)
    now = datetime.now(timezone.utc).isoformat()

    existing: dict = {}
    if log_path.exists():
        try:
            existing = json.loads(log_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}

    messages = data.get("messages", [])
    normalized_messages = []
    for msg in messages:
        entry = dict(msg)
        if "ts" not in entry:
            entry["ts"] = now
        normalized_messages.append(entry)

    payload = {
        "schema_version": CONVERSATION_LOG_SCHEMA_VERSION,
        "session_id": data.get("session_id"),
        "client_name": data.get("client_name"),
        "ref_id": data.get("ref_id"),
        "consent_ts": data.get("consent_ts"),
        "created_at": existing.get("created_at") or data.get("created_at") or now,
        "updated_at": now,
        "brief_version": data.get("brief_version", existing.get("brief_version", 1)),
        "messages": normalized_messages,
        "requirements": data.get("requirements", {}),
        "assets": data.get("assets", []),
    }

    log_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return log_path
