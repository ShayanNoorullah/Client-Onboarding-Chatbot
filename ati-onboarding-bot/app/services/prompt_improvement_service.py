import logging

from app.models.learning_models import LearningExample, PromptVersion
from app.services.prompt_registry import create_shadow_version, get_active_prompt

logger = logging.getLogger(__name__)

_pending_examples: list[str] = []
_pending_tasks: list[tuple[str, str]] = []


async def enqueue_failure_analysis(example_id: str) -> None:
    if example_id not in _pending_examples:
        _pending_examples.append(example_id)


async def enqueue_task_improvement(tenant_id: str, task_type: str) -> None:
    key = (tenant_id, task_type)
    if key not in _pending_tasks:
        _pending_tasks.append(key)


async def process_pending_improvements() -> int:
    processed = 0
    while _pending_examples:
        example_id = _pending_examples.pop(0)
        try:
            if await analyze_failure(example_id):
                processed += 1
        except Exception:
            logger.exception("Failed to analyze failure %s", example_id)

    while _pending_tasks:
        tenant_id, task_type = _pending_tasks.pop(0)
        try:
            example = await LearningExample.find_one(
                LearningExample.tenant_id == tenant_id,
                LearningExample.task_type == task_type,
                LearningExample.label == "failure",
            )
            if example:
                if await analyze_failure(str(example.id)):
                    processed += 1
        except Exception:
            logger.exception("Failed task improvement for %s", task_type)

    return processed


async def analyze_failure(example_id: str) -> bool:
    example = await LearningExample.get(example_id)
    if not example or example.label != "failure":
        return False

    prompt_name = example.prompt_name or "slm"
    if prompt_name not in ("slm", "summary_extraction"):
        prompt_name = "slm"

    active_content, active_version = await get_active_prompt(prompt_name, example.tenant_id)
    constraint = _derive_constraint(example)
    if not constraint:
        return False

    if constraint in active_content:
        return False

    patched = active_content.rstrip() + f"\n\nLearned constraint (from feedback):\n- {constraint}\n"
    await create_shadow_version(
        tenant_id=example.tenant_id,
        name=prompt_name,
        content=patched,
        parent_version_id=active_version,
        patch_rationale=example.comment or f"Failure on {example.task_type}",
    )

    from app.services.prompt_validation_service import validate_latest_shadow

    await validate_latest_shadow(example.tenant_id, prompt_name)
    return True


def _derive_constraint(example: LearningExample) -> str:
    if example.comment.strip():
        return example.comment.strip()[:300]
    if example.user_input.strip():
        return f"When user says '{example.user_input[:120]}', respond more accurately and concisely."
    return "Prioritize clarity and accuracy based on recent negative feedback."


async def list_shadow_versions(tenant_id: str) -> list[dict]:
    docs = await PromptVersion.find(
        PromptVersion.tenant_id == tenant_id,
        PromptVersion.status == "shadow",
    ).to_list()
    return [d.to_dict() for d in docs]
