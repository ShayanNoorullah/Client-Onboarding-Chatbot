import pytest
from cryptography.fernet import Fernet

from app.storage.encryptor import decrypt_log, encrypt_log


@pytest.fixture
def encryption_key(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setattr("app.config.settings.ENCRYPTION_KEY", key)
    return key


def test_encrypt_decrypt_roundtrip(tmp_path, encryption_key):
    log_path = tmp_path / "conversation_log.json"
    data = {
        "session_id": "test-123",
        "client_name": "Sarah_Johnson",
        "messages": [
            {"role": "user", "content": "I need a website"},
            {"role": "assistant", "content": "Tell me more!"},
        ],
    }

    encrypt_log(data, log_path)
    assert log_path.exists()

    raw = log_path.read_bytes()
    assert b"session_id" not in raw

    decrypted = decrypt_log(log_path)
    assert decrypted["session_id"] == "test-123"
    assert decrypted["client_name"] == "Sarah_Johnson"
    assert len(decrypted["messages"]) == 2


def test_missing_encryption_key_raises(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.ENCRYPTION_KEY", "")
    with pytest.raises(ValueError, match="ENCRYPTION_KEY"):
        encrypt_log({}, tmp_path / "log.json")
