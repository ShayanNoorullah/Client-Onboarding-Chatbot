from datetime import datetime, timezone
from typing import Any

from beanie import Document, Indexed
from pydantic import Field


class TurnRecord(Document):
    tenant_id: str = "default"
    session_id: Indexed(str)
    turn_id: Indexed(str, unique=True)
    user_id: str | None = None
    stage: str = ""
    task_type: str = "requirements_chat"
    user_input: str = ""
    assistant_output: str = ""
    prompt_version: str = "v2.0"
    prompt_name: str = "slm"
    rag_context_hash: str = ""
    rag_sources_used: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "turn_records"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "turn_id": self.turn_id,
            "session_id": self.session_id,
            "stage": self.stage,
            "task_type": self.task_type,
            "created_at": self.created_at.isoformat(),
        }


class AgentFeedbackEvent(Document):
    tenant_id: str = "default"
    user_id: str | None = None
    session_id: str | None = None
    turn_id: str | None = None
    brief_id: str | None = None
    feedback_type: str  # thumbs_up, thumbs_down, step_approve, step_reject, correction, brief_rating
    signal: int = 0  # -1, 0, 1
    comment: str = ""
    task_type: str = ""
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "agent_feedback_events"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "feedback_type": self.feedback_type,
            "signal": self.signal,
            "comment": self.comment,
            "task_type": self.task_type,
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "brief_id": self.brief_id,
            "created_at": self.created_at.isoformat(),
        }


class LearningExample(Document):
    tenant_id: str = "default"
    task_type: str
    label: str  # success | failure
    user_input: str = ""
    assistant_output: str = ""
    prompt_version: str = ""
    prompt_name: str = "slm"
    feedback_signal: int = 0
    comment: str = ""
    session_id: str | None = None
    turn_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "learning_examples"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "task_type": self.task_type,
            "label": self.label,
            "feedback_signal": self.feedback_signal,
            "prompt_version": self.prompt_version,
            "created_at": self.created_at.isoformat(),
        }


class PromptVersion(Document):
    tenant_id: str = "default"
    name: str  # slm, summary_extraction
    version_id: str
    content: str
    status: str = "active"  # active | shadow | retired
    parent_version_id: str | None = None
    patch_rationale: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "prompt_versions"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "version_id": self.version_id,
            "status": self.status,
            "parent_version_id": self.parent_version_id,
            "patch_rationale": self.patch_rationale,
            "created_at": self.created_at.isoformat(),
        }


class PromptValidationRun(Document):
    tenant_id: str = "default"
    prompt_version_id: str
    prompt_name: str
    failures_fixed: int = 0
    regressions: int = 0
    confidence: float = 0.0
    promoted: bool = False
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "prompt_validation_runs"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "prompt_version_id": self.prompt_version_id,
            "prompt_name": self.prompt_name,
            "failures_fixed": self.failures_fixed,
            "regressions": self.regressions,
            "confidence": self.confidence,
            "promoted": self.promoted,
            "created_at": self.created_at.isoformat(),
        }


class LearnedPatternRecord(Document):
    tenant_id: str = "default"
    line: str
    project_type: str = ""
    quality_score: float = 1.0
    source: str = "session"
    deprecated: bool = False
    session_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "learned_pattern_records"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "line": self.line,
            "project_type": self.project_type,
            "quality_score": self.quality_score,
            "deprecated": self.deprecated,
            "created_at": self.created_at.isoformat(),
        }


class TaskAccuracySnapshot(Document):
    tenant_id: str = "default"
    task_type: str
    accuracy_pct: float = 100.0
    positive_count: int = 0
    negative_count: int = 0
    window_days: int = 30
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "task_accuracy_snapshots"

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_type": self.task_type,
            "accuracy_pct": self.accuracy_pct,
            "positive_count": self.positive_count,
            "negative_count": self.negative_count,
            "updated_at": self.updated_at.isoformat(),
        }
