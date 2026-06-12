from app.models.system_config import SystemConfig
from app.services.email_service import _normalize_emails, render_template


def test_normalize_emails_single_and_list():
    assert _normalize_emails("a@x.com") == ["a@x.com"]
    assert _normalize_emails(["a@x.com", "", " b@x.com "]) == ["a@x.com", "b@x.com"]
    assert _normalize_emails(None) == []


def test_system_config_notification_fields():
    cfg = SystemConfig.model_construct(
        tenant_id="default",
        notification_to_emails=["admin@example.com"],
        notification_cc_emails=["cc@example.com"],
    )
    data = cfg.to_dict()
    assert data["notification_to_emails"] == ["admin@example.com"]
    assert data["notification_cc_emails"] == ["cc@example.com"]


def test_brief_submitted_admin_template_vars():
    html = (
        "<p>{{client_name}} — {{user_email}} — {{project_type}} — "
        "<a href=\"{{brief_link}}\">link</a> — {{ref_id}}</p>"
    )
    out = render_template(html, {
        "client_name": "Acme",
        "user_email": "u@acme.com",
        "project_type": "mobile_app",
        "brief_link": "/api/briefs/1/download",
        "ref_id": "Acme_2026",
    })
    assert "Acme" in out
    assert "u@acme.com" in out
    assert "/api/briefs/1/download" in out
