from app.auth.tenant_context import get_user_tenant_id
from app.models.tenant import Tenant
from app.models.user import User


def test_tenant_model_defaults():
    tenant = Tenant.model_construct(slug="acme", name="Acme Corp")
    data = tenant.to_dict()
    assert data["slug"] == "acme"
    assert data["plan"] == "free"


def test_user_tenant_id_default():
    user = User.model_construct(
        email="u@example.com",
        full_name="User",
        password_hash="x",
        tenant_id="default",
    )
    pub = user.to_public()
    assert pub["tenant_id"] == "default"


def test_super_admin_can_override_tenant_header():
    user = User.model_construct(
        email="admin@example.com",
        full_name="Admin",
        password_hash="x",
        tenant_id="default",
        is_super_admin=True,
        role="admin",
    )

    class FakeRequest:
        headers = {"X-Tenant-ID": "acme"}

    assert get_user_tenant_id(user, FakeRequest()) == "acme"
