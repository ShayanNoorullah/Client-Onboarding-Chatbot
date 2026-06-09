import json
from pathlib import Path

from cryptography.fernet import Fernet

from app.config import settings


def _get_fernet() -> Fernet:
    if not settings.ENCRYPTION_KEY:
        raise ValueError("ENCRYPTION_KEY is not set in environment")
    return Fernet(settings.ENCRYPTION_KEY.encode())


def encrypt_log(data: dict, output_path: Path) -> None:
    """Encrypt conversation log JSON and write to disk."""
    f = _get_fernet()
    raw = json.dumps(data, ensure_ascii=False).encode()
    output_path.write_bytes(f.encrypt(raw))


def decrypt_log(input_path: Path) -> dict:
    """Decrypt and parse a conversation log."""
    f = _get_fernet()
    return json.loads(f.decrypt(input_path.read_bytes()).decode())
