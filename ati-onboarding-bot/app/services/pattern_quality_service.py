import logging
from datetime import datetime, timezone

from app.models.learning_models import AgentFeedbackEvent, LearnedPatternRecord

logger = logging.getLogger(__name__)

NEGATIVE_RATE_THRESHOLD = 0.5


async def deprecate_patterns_for_session(session_id: str) -> int:
    """Mark patterns from a negatively-rated session as deprecated."""
    patterns = await LearnedPatternRecord.find(
        LearnedPatternRecord.session_id == session_id,
        LearnedPatternRecord.deprecated == False,
    ).to_list()
    count = 0
    for p in patterns:
        p.deprecated = True
        p.quality_score = 0.0
        await p.save()
        count += 1
    return count


async def review_pattern_quality(tenant_id: str = "default") -> int:
    """Deprecate patterns linked to sessions with multiple negative feedback events."""
    patterns = await LearnedPatternRecord.find(
        LearnedPatternRecord.tenant_id == tenant_id,
        LearnedPatternRecord.deprecated == False,
    ).to_list()
    deprecated = 0
    for pattern in patterns:
        if not pattern.session_id:
            continue
        negatives = await AgentFeedbackEvent.find(
            AgentFeedbackEvent.session_id == pattern.session_id,
            AgentFeedbackEvent.signal < 0,
        ).count()
        positives = await AgentFeedbackEvent.find(
            AgentFeedbackEvent.session_id == pattern.session_id,
            AgentFeedbackEvent.signal > 0,
        ).count()
        total = negatives + positives
        if total >= 2 and (negatives / total) >= NEGATIVE_RATE_THRESHOLD:
            pattern.deprecated = True
            pattern.quality_score = max(0.0, pattern.quality_score - 0.5)
            await pattern.save()
            deprecated += 1
    if deprecated:
        from app.services.kb_reindex import reindex_learned_patterns

        await _sync_patterns_file(tenant_id)
        reindex_learned_patterns()
    return deprecated


async def _sync_patterns_file(tenant_id: str) -> None:
    from app.config import settings

    patterns = await LearnedPatternRecord.find(
        LearnedPatternRecord.tenant_id == tenant_id,
        LearnedPatternRecord.deprecated == False,
    ).to_list()
    path = settings.ATI_KB_ROOT / "learned_patterns.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [p.line if p.line.endswith("\n") else p.line + "\n" for p in patterns]
    path.write_text("".join(lines), encoding="utf-8")


async def get_learned_constraints(tenant_id: str = "default", limit: int = 5) -> list[str]:
    patterns = await LearnedPatternRecord.find(
        LearnedPatternRecord.tenant_id == tenant_id,
        LearnedPatternRecord.deprecated == False,
    ).sort(-LearnedPatternRecord.quality_score).limit(limit).to_list()
    return [p.line.strip() for p in patterns if p.line.strip()]
