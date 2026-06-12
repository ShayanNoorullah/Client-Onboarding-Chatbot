from app.db.seeders import build_permissions_map, _canonical_project_types, _default_page_defs


def test_canonical_project_types():
    types = _canonical_project_types()
    assert "website_development" in types
    assert "consulting" in types
    assert len(types) == 5


def test_default_pages_include_settings_and_pipeline():
    pages = _default_page_defs()
    modules = {p["module_name"] for p in pages}
    assert "Settings" in modules
    assert "Pipeline" in modules
    assert "Configuration" in modules
    names = [p["page_name"] for p in pages if p["module_name"] == "Settings"]
    assert "User" in names
    assert "Role" in names


def test_build_permissions_full_access():
    perms = build_permissions_map(full_access=True)
    assert perms["Settings"]["User"]["view"] is True
    assert perms["Settings"]["User"]["delete"] is True


def test_build_permissions_user_limited():
    perms = build_permissions_map(full_access=False)
    assert perms["Dashboard"]["Dashboard"]["view"] is True
    assert perms["Settings"]["User"]["view"] is False
    assert perms["Pipeline"]["Onboarding Sessions"]["view"] is True
