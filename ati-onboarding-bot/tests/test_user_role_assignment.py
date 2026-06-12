import pytest
from fastapi import HTTPException

from app.api.settings_routes import (
    ADMIN_ROLE,
    SUPER_ADMIN_ROLE,
    _actor_is_super_admin,
    _target_is_super_admin,
    _validate_role_assignment,
)
from app.models.role import Role
from app.models.user import User


def _user(**kwargs) -> User:
    return User.model_construct(
        email="u@test.com",
        full_name="Test",
        **kwargs,
    )


def _patch_role_lookup(monkeypatch, role: Role | None):
    async def mock_get_role(_role_name: str):
        return role

    monkeypatch.setattr("app.api.settings_routes._get_role_by_name", mock_get_role)


def test_actor_and_target_super_admin_flags():
    assert _actor_is_super_admin(_user(role_name=SUPER_ADMIN_ROLE, is_super_admin=True))
    assert _target_is_super_admin(_user(role_name=SUPER_ADMIN_ROLE))
    assert not _actor_is_super_admin(_user(role_name=ADMIN_ROLE))


@pytest.mark.asyncio
async def test_cannot_assign_super_admin_role():
    actor = _user(role_name=SUPER_ADMIN_ROLE, is_super_admin=True)
    with pytest.raises(HTTPException) as exc:
        await _validate_role_assignment(actor, SUPER_ADMIN_ROLE)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_admin_cannot_assign_admin_role(monkeypatch):
    actor = _user(role_name=ADMIN_ROLE, role="admin")
    _patch_role_lookup(monkeypatch, Role.model_construct(name=ADMIN_ROLE, is_active=True))
    with pytest.raises(HTTPException) as exc:
        await _validate_role_assignment(actor, ADMIN_ROLE)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_super_admin_can_assign_admin_role(monkeypatch):
    actor = _user(role_name=SUPER_ADMIN_ROLE, is_super_admin=True)
    _patch_role_lookup(monkeypatch, Role.model_construct(name=ADMIN_ROLE, is_active=True))
    await _validate_role_assignment(actor, ADMIN_ROLE)


@pytest.mark.asyncio
async def test_admin_can_assign_custom_role(monkeypatch):
    actor = _user(role_name=ADMIN_ROLE, role="admin")
    _patch_role_lookup(monkeypatch, Role.model_construct(name="Project Lead", is_active=True))
    await _validate_role_assignment(actor, "Project Lead")


@pytest.mark.asyncio
async def test_cannot_change_super_admin_user_role(monkeypatch):
    actor = _user(role_name=SUPER_ADMIN_ROLE, is_super_admin=True)
    target = _user(role_name=SUPER_ADMIN_ROLE, is_super_admin=True)
    _patch_role_lookup(monkeypatch, Role.model_construct(name=ADMIN_ROLE, is_active=True))
    with pytest.raises(HTTPException) as exc:
        await _validate_role_assignment(actor, ADMIN_ROLE, target_user=target)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_admin_cannot_demote_other_admin(monkeypatch):
    actor = _user(role_name=ADMIN_ROLE, role="admin")
    target = _user(role_name=ADMIN_ROLE, role="admin")
    _patch_role_lookup(monkeypatch, Role.model_construct(name="User", is_active=True))
    with pytest.raises(HTTPException) as exc:
        await _validate_role_assignment(actor, "User", target_user=target)
    assert exc.value.status_code == 403
