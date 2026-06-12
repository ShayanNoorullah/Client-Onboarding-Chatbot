from main import app


def _route_paths():
    return [getattr(r, "path", "") for r in app.routes if hasattr(r, "path")]


def test_config_ai_route_registered():
    paths = _route_paths()
    assert "/api/admin/config/ai" in paths


def test_config_system_route_registered():
    paths = _route_paths()
    assert "/api/admin/config/system" in paths


def test_audit_route_registered():
    paths = _route_paths()
    assert "/api/admin/audit" in paths


def test_tenant_current_route_registered():
    paths = _route_paths()
    assert "/api/admin/tenants/current" in paths
