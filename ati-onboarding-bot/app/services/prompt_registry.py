import logging
import uuid
from datetime import datetime, timezone

from app.agent import prompts as prompt_module
from app.models.learning_models import PromptVersion
from app.services.ai_config_service import get_effective_ai_settings

logger = logging.getLogger(__name__)

PROMPT_SEEDS = {
    "slm": prompt_module.SLM_SYSTEM_PROMPT,
    "summary_extraction": prompt_module.SUMMARY_EXTRACTION_PROMPT,
}

async def ensure_prompt_seeds(tenant_id: str = "default") -> None:
    for name, content in PROMPT_SEEDS.items():
        active = await PromptVersion.find_one(
            PromptVersion.tenant_id == tenant_id,
            PromptVersion.name == name,
            PromptVersion.status == "active",
        )
        if not active:
            await PromptVersion(
                tenant_id=tenant_id,
                name=name,
                version_id="v2.0",
                content=content,
                status="active",
            ).insert()


async def get_active_prompt(name: str, tenant_id: str = "default") -> tuple[str, str]:
    """Return (content, version_id)."""
    await ensure_prompt_seeds(tenant_id)

    doc = await PromptVersion.find_one(
        PromptVersion.tenant_id == tenant_id,
        PromptVersion.name == name,
        PromptVersion.status == "active",
    )
    if not doc:
        cfg = await get_effective_ai_settings(tenant_id)
        return PROMPT_SEEDS.get(name, ""), cfg.get("prompt_version", "v2.0")

    return doc.content, doc.version_id


def invalidate_prompt_cache() -> None:
    pass


async def create_shadow_version(
    *,
    tenant_id: str,
    name: str,
    content: str,
    parent_version_id: str,
    patch_rationale: str,
) -> PromptVersion:
    version_id = f"{parent_version_id}-{uuid.uuid4().hex[:8]}"
    doc = PromptVersion(
        tenant_id=tenant_id,
        name=name,
        version_id=version_id,
        content=content,
        status="shadow",
        parent_version_id=parent_version_id,
        patch_rationale=patch_rationale,
    )
    await doc.insert()
    return doc


async def promote_shadow(shadow: PromptVersion) -> None:
    active = await PromptVersion.find_one(
        PromptVersion.tenant_id == shadow.tenant_id,
        PromptVersion.name == shadow.name,
        PromptVersion.status == "active",
    )
    if active:
        active.status = "retired"
        await active.save()

    shadow.status = "active"
    await shadow.save()
    invalidate_prompt_cache()

    from app.models.ai_config import AiConfig

    cfg = await AiConfig.find_one(AiConfig.tenant_id == shadow.tenant_id)
    if cfg:
        cfg.prompt_version = shadow.version_id
        cfg.updated_at = datetime.now(timezone.utc)
        await cfg.save()
