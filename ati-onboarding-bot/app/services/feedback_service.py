import logging
import uuid
from typing import Any

from app.models.learning_models import AgentFeedbackEvent, LearningExample, TurnRecord
from app.services.accuracy_service import record_feedback_accuracy

logger = logging.getLogger(__name__)

STAGE_TASK_MAP = {
    "greeting": "requirements_chat",
    "consent": "consent",
    "identity": "identity",
    "requirements": "requirements_chat",
    "clarify": "clarify_chat",
    "summarise": "brief_extraction",
    "done": "brief_generation",
}


def task_type_for_stage(stage: str) -> str:
    return STAGE_TASK_MAP.get(stage, "requirements_chat")


async def record_turn(
    *,
    tenant_id: str,
    session_id: str,
    user_id: str | None,
    stage: str,
    user_input: str,
    assistant_output: str,
    prompt_version: str,
    rag_context_hash: str = "",
    rag_sources_used: list[str] | None = None,
) -> str:
    turn_id = str(uuid.uuid4())
    rec = TurnRecord(
        tenant_id=tenant_id,
        session_id=session_id,
        turn_id=turn_id,
        user_id=user_id,
        stage=stage,
        task_type=task_type_for_stage(stage),
        user_input=user_input[:4000],
        assistant_output=assistant_output[:4000],
        prompt_version=prompt_version,
        rag_context_hash=rag_context_hash,
        rag_sources_used=rag_sources_used or [],
    )
    await rec.insert()
    return turn_id


async def ingest_feedback(
    *,
    tenant_id: str,
    user_id: str | None,
    feedback_type: str,
    signal: int,
    comment: str = "",
    session_id: str | None = None,
    turn_id: str | None = None,
    brief_id: str | None = None,
    task_type: str = "",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = AgentFeedbackEvent(
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
        turn_id=turn_id,
        brief_id=brief_id,
        feedback_type=feedback_type,
        signal=signal,
        comment=comment[:2000],
        task_type=task_type,
        context=context or {},
    )
    await event.insert()

    example = await _build_learning_example(event)
    if example:
        await example.insert()
        if signal < 0:
            from app.services.prompt_improvement_service import enqueue_failure_analysis

            await enqueue_failure_analysis(str(example.id))

    if task_type:
        await record_feedback_accuracy(tenant_id, task_type, signal)

    return {"event": event.to_dict(), "example_id": str(example.id) if example else None}


async def _build_learning_example(event: AgentFeedbackEvent) -> LearningExample | None:
    user_input = ""
    assistant_output = ""
    prompt_version = ""
    task_type = event.task_type or "requirements_chat"

    if event.turn_id:
        turn = await TurnRecord.find_one(TurnRecord.turn_id == event.turn_id)
        if turn:
            user_input = turn.user_input
            assistant_output = turn.assistant_output
            prompt_version = turn.prompt_version
            task_type = turn.task_type

    label = "success" if event.signal > 0 else "failure" if event.signal < 0 else "neutral"
    if label == "neutral":
        return None

    return LearningExample(
        tenant_id=event.tenant_id,
        task_type=task_type,
        label=label,
        user_input=user_input,
        assistant_output=assistant_output,
        prompt_version=prompt_version,
        feedback_signal=event.signal,
        comment=event.comment,
        session_id=event.session_id,
        turn_id=event.turn_id,
    )


async def session_has_negative_feedback(session_id: str) -> bool:
    neg = await AgentFeedbackEvent.find_one(
        AgentFeedbackEvent.session_id == session_id,
        AgentFeedbackEvent.signal < 0,
    )
    return neg is not None
