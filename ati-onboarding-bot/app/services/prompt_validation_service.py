import logging

from app.models.learning_models import LearningExample, PromptValidationRun, PromptVersion
from app.services.prompt_registry import promote_shadow

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.85
MAX_REPLAY = 20


async def validate_latest_shadow(tenant_id: str, prompt_name: str) -> PromptValidationRun | None:
    shadow = await PromptVersion.find_one(
        PromptVersion.tenant_id == tenant_id,
        PromptVersion.name == prompt_name,
        PromptVersion.status == "shadow",
    )
    if not shadow:
        return None
    return await validate_shadow_version(shadow)


async def validate_shadow_version(shadow: PromptVersion) -> PromptValidationRun:
    failures = await LearningExample.find(
        LearningExample.tenant_id == shadow.tenant_id,
        LearningExample.prompt_name == shadow.name,
        LearningExample.label == "failure",
    ).sort(-LearningExample.created_at).limit(MAX_REPLAY).to_list()

    successes = await LearningExample.find(
        LearningExample.tenant_id == shadow.tenant_id,
        LearningExample.prompt_name == shadow.name,
        LearningExample.label == "success",
    ).sort(-LearningExample.created_at).limit(MAX_REPLAY).to_list()

    failures_fixed = 0
    regressions = 0

    for ex in failures:
        if _shadow_addresses_failure(shadow.content, ex):
            failures_fixed += 1

    for ex in successes:
        if _would_regress(shadow.content, ex):
            regressions += 1

    total = max(len(failures) + len(successes), 1)
    confidence = round((failures_fixed + len(successes) - regressions) / total, 2)
    confidence = min(max(confidence, 0.0), 1.0)

    promoted = failures_fixed > 0 and regressions == 0 and confidence >= CONFIDENCE_THRESHOLD
    run = PromptValidationRun(
        tenant_id=shadow.tenant_id,
        prompt_version_id=shadow.version_id,
        prompt_name=shadow.name,
        failures_fixed=failures_fixed,
        regressions=regressions,
        confidence=confidence,
        promoted=promoted,
        details={"failure_count": len(failures), "success_count": len(successes)},
    )
    await run.insert()

    if promoted:
        await promote_shadow(shadow)
        logger.info("Promoted shadow prompt %s for %s", shadow.version_id, shadow.name)

    return run


def _shadow_addresses_failure(shadow_content: str, example: LearningExample) -> bool:
    if example.comment and example.comment[:40] in shadow_content:
        return True
    if "Learned constraint" in shadow_content and example.label == "failure":
        return True
    return False


def _would_regress(shadow_content: str, example: LearningExample) -> bool:
    if not example.assistant_output:
        return False
    return len(shadow_content) > 12000


async def process_pending_validations(tenant_id: str = "default") -> int:
    shadows = await PromptVersion.find(
        PromptVersion.tenant_id == tenant_id,
        PromptVersion.status == "shadow",
    ).to_list()
    count = 0
    for shadow in shadows:
        existing = await PromptValidationRun.find_one(
            PromptValidationRun.prompt_version_id == shadow.version_id,
            PromptValidationRun.promoted == True,
        )
        if existing:
            continue
        await validate_shadow_version(shadow)
        count += 1
    return count
