from app.models.email_template import EmailTemplate
from app.services.email_service import render_template


def test_render_template_variables():
    result = render_template("Hello {{client_name}}, welcome to {{product_name}}", {
        "client_name": "Jane",
        "product_name": "COA",
    })
    assert result == "Hello Jane, welcome to COA"


def test_email_template_to_dict():
    tpl = EmailTemplate.model_construct(
        tenant_id="default",
        key="welcome",
        name="Welcome",
        subject="Hi",
        body_html="<p>Hi</p>",
    )
    data = tpl.to_dict()
    assert data["key"] == "welcome"
    assert data["tenant_id"] == "default"
