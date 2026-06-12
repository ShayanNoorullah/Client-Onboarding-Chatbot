from app.storage.file_manager import create_client_workspace
from app.storage.summary_writer import write_summary


def test_write_summary_all_sections(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.STORAGE_ROOT", tmp_path)

    folder = create_client_workspace("Sarah Johnson")
    state = {
        "client_name": "Sarah_Johnson",
        "session_id": "sess-abc-123",
        "consent_ts": "2026-06-08 12:00 UTC",
        "requirements": {
            "project_summary": "Mortgage company website with loan application form.",
            "items": [
                "Home, About, Services, Contact pages",
                "Loan application form integration",
                "8-week launch timeline",
            ],
            "contact_preference": "Email",
            "recommended_services": [
                "Mortgage Website Development Services",
                "Custom Mortgage Development",
            ],
            "security_requirements": ["HTTPS everywhere", "Role-based access"],
            "compliance_requirements": ["GLBA alignment"],
            "data_handling": "PII stored in US-only cloud with encryption at rest.",
            "integration_access": ["Encompass LOS API", "Salesforce CRM"],
        },
        "assets": [str(folder / "assets" / "homepage_inspo.jpg")],
        "asset_descriptions": {
            str(folder / "assets" / "homepage_inspo.jpg"): "Clean navy and gold layout",
        },
    }

    summary_path = write_summary(folder, state)
    content = summary_path.read_text(encoding="utf-8")

    assert "# CLIENT BRIEF — Sarah_Johnson" in content
    assert "## 1. Client Information" in content
    assert "## 2. Project Overview" in content
    assert "## 3. Requirements" in content
    assert "## 4. Provided Assets" in content
    assert "## 5. ATI Services Recommended" in content
    assert "## 6. Security Requirements" in content
    assert "## 7. Compliance & Regulatory" in content
    assert "## 8. Data Handling" in content
    assert "## 9. Integration & Access" in content
    assert "## 10. Next Steps" in content
    assert "HTTPS everywhere" in content
    assert "GLBA alignment" in content
    assert "Encompass LOS API" in content
    assert "Mortgage Website Development Services" in content
    assert "homepage_inspo.jpg" in content
    assert "support@awesometechinc.com" in content
    assert "877-284-4968" in content
