import logging
from typing import Any

import httpx

from app.models.system_config import SystemConfig
from app.storage.encryptor import decrypt_text

logger = logging.getLogger(__name__)


async def create_nda_submission(
    tenant_id: str,
    *,
    submitter_email: str,
    submitter_name: str,
    template_id: str | None = None,
) -> tuple[bool, dict[str, Any] | str]:
    doc = await SystemConfig.find_one(SystemConfig.tenant_id == tenant_id)
    api_url = (doc.docuseal_api_url if doc else "").rstrip("/")
    api_key = ""
    if doc and doc.docuseal_api_key:
        try:
            api_key = decrypt_text(doc.docuseal_api_key)
        except Exception:
            api_key = doc.docuseal_api_key
    tid = template_id or (doc.docuseal_nda_template_id if doc else "")

    if not api_url or not api_key or not tid:
        return False, "DocuSeal not configured (api_url, api_key, template_id)"

    payload = {
        "template_id": int(tid) if str(tid).isdigit() else tid,
        "send_email": True,
        "submitters": [{"role": "Client", "email": submitter_email, "name": submitter_name}],
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{api_url}/submissions",
                json=payload,
                headers={"X-Auth-Token": api_key, "Content-Type": "application/json"},
            )
        if resp.status_code >= 400:
            return False, f"DocuSeal error {resp.status_code}: {resp.text[:300]}"
        return True, resp.json()
    except Exception as e:
        logger.exception("DocuSeal request failed")
        return False, str(e)
