from app.services.magic_link_service import (
    MAGIC_LINK_PURPOSE,
    PORTAL_PURPOSE,
    create_magic_token,
    create_portal_token,
    decode_token,
)


def test_portal_token_roundtrip():
    token = create_portal_token(brief_id="brief123", tenant_id="default", days=1)
    payload = decode_token(token, PORTAL_PURPOSE)
    assert payload is not None
    assert payload["brief_id"] == "brief123"
    assert payload["tenant_id"] == "default"


def test_magic_link_token_roundtrip():
    token = create_magic_token(user_id="user1", session_id="sess1", hours=1)
    payload = decode_token(token, MAGIC_LINK_PURPOSE)
    assert payload is not None
    assert payload["sub"] == "user1"
    assert payload["session_id"] == "sess1"
