import hashlib
import hmac

from app.models.webhook_subscription import WebhookSubscription
from app.services.webhook_dispatcher import _sign_payload


def test_webhook_sign_payload():
    secret = "test-secret"
    body = b'{"event":"test"}'
    sig = _sign_payload(secret, body)
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert sig == expected


def test_webhook_subscription_to_dict_masks_secret():
    sub = WebhookSubscription.model_construct(name="CRM", url="https://example.com/hook", secret="abc")
    data = sub.to_dict(mask_secret=True)
    assert data["secret"] == "••••••••"
