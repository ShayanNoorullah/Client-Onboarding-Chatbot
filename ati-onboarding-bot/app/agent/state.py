from typing import Any, TypedDict


class OnboardingState(TypedDict):
    messages: list[dict]
    client_name: str | None
    consent_given: bool
    consent_ts: str | None
    requirements: dict[str, Any]
    assets: list[str]
    asset_descriptions: dict[str, str]
    stage: str
    summary_written: bool
    session_id: str
    file_context: str
    ref_id: str | None
    pending_reply: str
    done: bool
    requirements_asked: int
    collected_requirements: dict[str, str]
    requirements_complete: bool
    readiness_score: float
    missing_fields: list[str]
    user_id: str | None
    brief_id: str | None
    consent_prompt_sent: bool
    auto_summarising: bool
    workspace_slug: str | None
    requirements_turn_count: int
    slm_readiness_complete: bool
    consent_pending_slm: bool
    user_memory_facts: list[str]
    manual_brief_requested: bool
    brief_update_pending: bool
    brief_version: int


def default_state() -> OnboardingState:
    return {
        "messages": [],
        "client_name": None,
        "consent_given": False,
        "consent_ts": None,
        "requirements": {},
        "assets": [],
        "asset_descriptions": {},
        "stage": "greeting",
        "summary_written": False,
        "session_id": "",
        "file_context": "",
        "ref_id": None,
        "pending_reply": "",
        "done": False,
        "requirements_asked": 0,
        "collected_requirements": {},
        "requirements_complete": False,
        "readiness_score": 0.0,
        "missing_fields": [],
        "user_id": None,
        "brief_id": None,
        "consent_prompt_sent": False,
        "auto_summarising": False,
        "workspace_slug": None,
        "requirements_turn_count": 0,
        "slm_readiness_complete": False,
        "consent_pending_slm": False,
        "user_memory_facts": [],
        "manual_brief_requested": False,
        "brief_update_pending": False,
        "brief_version": 1,
    }
