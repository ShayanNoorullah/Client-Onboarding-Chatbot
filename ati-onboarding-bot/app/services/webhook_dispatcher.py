import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone

import httpx

from app.models.webhook_delivery import WebhookDelivery
from app.models.webhook_subscription import WebhookSubscription

logger = logging.getLogger(__name__)


def _sign_payload(secret: str, body: bytes) -> str:
    if not secret:
        return ""
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


async def deliver_webhook(
    subscription: WebhookSubscription,
    event_type: str,
    payload: dict,
) -> WebhookDelivery:
    delivery = WebhookDelivery(
        tenant_id=subscription.tenant_id,
        subscription_id=str(subscription.id),
        event_type=event_type,
        payload=payload,
    )
    await delivery.insert()

    envelope = {
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": payload,
    }
    body = json.dumps(envelope).encode()
    headers = {"Content-Type": "application/json"}
    if subscription.secret:
        headers["X-Webhook-Signature"] = _sign_payload(subscription.secret, body)

    max_attempts = max(1, subscription.max_retries)
    for attempt in range(1, max_attempts + 1):
        delivery.attempts = attempt
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(subscription.url, content=body, headers=headers)
            delivery.response_status = resp.status_code
            if 200 <= resp.status_code < 300:
                delivery.status = "delivered"
                delivery.delivered_at = datetime.now(timezone.utc)
                await delivery.save()
                return delivery
            delivery.last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
        except Exception as e:
            delivery.last_error = str(e)
            logger.warning("Webhook delivery failed attempt %s: %s", attempt, e)

    delivery.status = "failed"
    await delivery.save()
    return delivery


async def dispatch_webhooks(tenant_id: str, event_type: str, payload: dict) -> list[WebhookDelivery]:
    subs = await WebhookSubscription.find(
        WebhookSubscription.tenant_id == tenant_id,
        WebhookSubscription.is_active == True,
    ).to_list()
    results = []
    for sub in subs:
        if sub.event_types and event_type not in sub.event_types:
            continue
        results.append(await deliver_webhook(sub, event_type, payload))
    return results
