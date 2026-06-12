from fastapi import APIRouter, Depends, Query, Request

from app.api.schemas import FeedbackSubmitRequest
from app.auth.dependencies import get_current_user, require_permission
from app.auth.tenant_context import get_user_tenant_id
from app.models.learning_models import AgentFeedbackEvent, LearnedPatternRecord, PromptValidationRun, PromptVersion
from app.models.user import User
from app.services.accuracy_service import get_accuracy_summary
from app.services.feedback_service import ingest_feedback, task_type_for_stage
from app.services.prompt_improvement_service import list_shadow_versions
from app.services.prompt_registry import ensure_prompt_seeds

router = APIRouter(tags=["learning"])


def _tenant_id(user: User, request: Request) -> str:
    return get_user_tenant_id(user, request)


@router.post("/api/feedback")
async def submit_feedback(body: FeedbackSubmitRequest, user: User = Depends(get_current_user)):
    tenant_id = user.tenant_id or "default"
    signal = body.signal
    if body.feedback_type == "brief_rating" and body.rating is not None:
        signal = 1 if body.rating >= 4 else -1 if body.rating <= 2 else 0
    elif signal == 0:
        if body.feedback_type in ("thumbs_up", "step_approve"):
            signal = 1
        elif body.feedback_type in ("thumbs_down", "step_reject"):
            signal = -1

    task_type = body.task_type or (task_type_for_stage(body.stage or "") if body.stage else "")
    result = await ingest_feedback(
        tenant_id=tenant_id,
        user_id=str(user.id),
        feedback_type=body.feedback_type,
        signal=signal,
        comment=body.comment,
        session_id=body.session_id,
        turn_id=body.turn_id,
        brief_id=body.brief_id,
        task_type=task_type,
        context=body.context,
    )
    return result


@router.get("/api/admin/learning/report")
async def learning_report(
    request: Request,
    admin: User = Depends(require_permission("Configuration", "Learning", "view")),
):
    tenant_id = _tenant_id(admin, request)
    await ensure_prompt_seeds(tenant_id)

    accuracy = await get_accuracy_summary(tenant_id)
    recent_feedback = await AgentFeedbackEvent.find(
        AgentFeedbackEvent.tenant_id == tenant_id
    ).sort(-AgentFeedbackEvent.created_at).limit(20).to_list()

    active_prompts = await PromptVersion.find(
        PromptVersion.tenant_id == tenant_id,
        PromptVersion.status == "active",
    ).to_list()
    shadows = await list_shadow_versions(tenant_id)
    validations = await PromptValidationRun.find(
        PromptValidationRun.tenant_id == tenant_id
    ).sort(-PromptValidationRun.created_at).limit(10).to_list()
    deprecated = await LearnedPatternRecord.find(
        LearnedPatternRecord.tenant_id == tenant_id,
        LearnedPatternRecord.deprecated == True,
    ).limit(20).to_list()

    promoted = [v for v in validations if v.promoted]
    return {
        "accuracy_by_task": accuracy,
        "recent_feedback": [f.to_dict() for f in recent_feedback],
        "active_prompts": [p.to_dict() for p in active_prompts],
        "shadow_prompts": shadows,
        "recent_validations": [v.to_dict() for v in validations],
        "promotions_count": len(promoted),
        "deprecated_patterns": [p.to_dict() for p in deprecated],
    }


@router.get("/api/admin/learning/feedback")
async def list_feedback(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    admin: User = Depends(require_permission("Configuration", "Learning", "view")),
):
    tenant_id = _tenant_id(admin, request)
    events = await AgentFeedbackEvent.find(
        AgentFeedbackEvent.tenant_id == tenant_id
    ).sort(-AgentFeedbackEvent.created_at).limit(limit).to_list()
    return {"feedback": [e.to_dict() for e in events]}
