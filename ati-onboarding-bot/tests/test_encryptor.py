import json

import pytest
from cryptography.fernet import Fernet

from app.storage.encryptor import decrypt_log, encrypt_log, get_encrypted_log_path
from app.storage.file_manager import write_conversation_log


@pytest.fixture
def encryption_key(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setattr("app.config.settings.ENCRYPTION_KEY", key)
    return key


def test_write_conversation_log_valid_json(tmp_path):
    data = {
        "session_id": "test-123",
        "client_name": "Sarah_Johnson",
        "ref_id": "Sarah_Johnson_2026-06-08",
        "consent_ts": "2026-06-08 12:00 UTC",
        "messages": [
            {"role": "user", "content": "I need a website"},
            {"role": "assistant", "content": "Tell me more!"},
        ],
        "requirements": {"project_summary": "A website"},
        "assets": [],
        "brief_version": 1,
    }
    write_conversation_log(tmp_path, data)
    log_path = tmp_path / "conversation_log.json"
    assert log_path.exists()
    parsed = json.loads(log_path.read_text(encoding="utf-8"))
    assert parsed["schema_version"] == 1
    assert parsed["session_id"] == "test-123"
    assert len(parsed["messages"]) == 2
    assert "created_at" in parsed
    assert "updated_at" in parsed


def test_encrypt_decrypt_roundtrip(tmp_path, encryption_key):
    json_path = tmp_path / "conversation_log.json"
    data = {
        "session_id": "test-123",
        "client_name": "Sarah_Johnson",
        "messages": [
            {"role": "user", "content": "I need a website"},
            {"role": "assistant", "content": "Tell me more!"},
        ],
    }

    write_conversation_log(tmp_path, data)
    encrypt_log(data, json_path)

    enc_path = get_encrypted_log_path(json_path)
    assert enc_path.exists()
    assert enc_path.suffix == ".enc"

    raw_json = json_path.read_text(encoding="utf-8")
    assert json.loads(raw_json)["session_id"] == "test-123"

    raw_enc = enc_path.read_bytes()
    assert b"session_id" not in raw_enc

    decrypted = decrypt_log(enc_path)
    assert decrypted["session_id"] == "test-123"
    assert decrypted["client_name"] == "Sarah_Johnson"
    assert len(decrypted["messages"]) == 2


def test_missing_encryption_key_raises(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.ENCRYPTION_KEY", "")
    with pytest.raises(ValueError, match="ENCRYPTION_KEY"):
        encrypt_log({}, tmp_path / "conversation_log.json")
