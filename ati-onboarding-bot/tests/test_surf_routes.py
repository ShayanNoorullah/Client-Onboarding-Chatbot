import pytest
from fastapi import HTTPException

from app.api import routes as chat_routes
from app.api.schemas import SurfUrlRequest
from app.models.user import User


def _fake_user() -> User:
    return User.model_construct(
        email="u@test.com",
        full_name="Test",
        tenant_id="default",
    )


@pytest.mark.asyncio
async def test_surf_url_requires_consent(monkeypatch):
    class FakeStore:
        async def get(self, session_id, user_id):
            return {
                "tenant_id": "default",
                "consent_given": False,
                "client_name": "Acme",
                "assets": [],
                "asset_descriptions": {},
            }

    monkeypatch.setattr(chat_routes, "mongo_session_store", FakeStore())
    user = _fake_user()

    with pytest.raises(HTTPException) as exc:
        await chat_routes.surf_url("sess1", SurfUrlRequest(url="https://example.com"), user)
    assert exc.value.status_code == 403
    assert "Consent" in exc.value.detail


@pytest.mark.asyncio
async def test_surf_url_respects_max_limit(monkeypatch):
    class FakeStore:
        async def get(self, session_id, user_id):
            return {
                "tenant_id": "default",
                "consent_given": True,
                "client_name": "Acme",
                "surfed_urls": ["https://a.com", "https://b.com"],
                "assets": [],
                "asset_descriptions": {},
            }

        async def update(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(chat_routes, "mongo_session_store", FakeStore())
    chat_routes._session_surf_counts["sess1"] = 2

    async def fake_settings(_tenant):
        return {"surf_enabled": True, "max_urls_per_session": 2}

    monkeypatch.setattr(
        "app.services.system_config_service.get_effective_settings",
        fake_settings,
    )

    user = _fake_user()
    with pytest.raises(HTTPException) as exc:
        await chat_routes.surf_url("sess1", SurfUrlRequest(url="https://example.com"), user)
    assert exc.value.status_code == 400
