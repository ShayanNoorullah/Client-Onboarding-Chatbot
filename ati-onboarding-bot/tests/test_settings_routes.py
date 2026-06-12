from app.api.settings_routes import _sync_role_field, ADMIN_ROLE_NAMES


def test_sync_role_field_admin_roles():
    assert _sync_role_field("Admin") == "admin"
    assert _sync_role_field("Super Admin") == "admin"
    assert _sync_role_field("User") == "user"


def test_admin_role_names_set():
    assert "Admin" in ADMIN_ROLE_NAMES
    assert "Super Admin" in ADMIN_ROLE_NAMES
