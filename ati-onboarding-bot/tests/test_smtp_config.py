from app.models.smtp_config import SmtpConfig


def test_smtp_config_masks_password():
    cfg = SmtpConfig.model_construct(
        smtp_host="smtp.example.com",
        smtp_port=587,
        password="encrypted-token",
    )
    data = cfg.to_dict(mask_password=True)
    assert data["password"] == "••••••••"
    assert data["smtp_host"] == "smtp.example.com"


def test_smtp_config_unmasked_when_requested():
    cfg = SmtpConfig.model_construct(password="secret")
    data = cfg.to_dict(mask_password=False)
    assert data["password"] == "secret"
