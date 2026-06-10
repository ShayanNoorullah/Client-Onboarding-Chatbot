from app.auth.jwt import create_access_token, decode_access_token
from app.auth.passwords import hash_password, verify_password


def test_password_hash_roundtrip():
    hashed = hash_password("TestPassword123!")
    assert verify_password("TestPassword123!", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_create_decode():
    token = create_access_token("user123", "user")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user123"
    assert payload["role"] == "user"


def test_jwt_invalid():
    assert decode_access_token("invalid.token.here") is None
