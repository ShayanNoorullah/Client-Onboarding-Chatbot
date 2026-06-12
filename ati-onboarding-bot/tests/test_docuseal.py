from app.models.system_config import SystemConfig


def test_docuseal_config_fields_present():
    cfg = SystemConfig.model_construct(
        docuseal_api_url="https://docuseal.example.com/api",
        docuseal_nda_template_id="1001",
    )
    data = cfg.to_dict()
    assert data["docuseal_api_url"] == "https://docuseal.example.com/api"
    assert data["docuseal_nda_template_id"] == "1001"
