from __future__ import annotations

from app.agent.state import OnboardingState

DONE_PHRASES = {
    "i'm done", "im done", "that's all", "thats all", "nothing else",
    "no more questions", "prepare my brief", "generate my brief",
    "i am done", "we're done", "were done", "all done", "finish up",
    "create the brief", "ready to go",
}

CONSENT_PHRASES = {
    "i agree", "agree", "yes i agree", "i consent", "consent",
    "yes", "sure", "ok", "okay", "sounds good", "yes i consent",
    "yes, i consent", "i accept", "accept",
}

AUTO_BRIEF_READINESS_THRESHOLD = 0.85


def is_consent_message(text: str) -> bool:
    normalized = text.strip().lower()
    if normalized in CONSENT_PHRASES:
        return True
    return normalized.startswith("i agree") or normalized.startswith("yes, i")


def is_ready_for_auto_brief(state: OnboardingState) -> bool:
    """Enough requirements collected — brief can be generated without user saying done."""
    if state.get("done"):
        return False
    if not state.get("requirements_complete"):
        return False
    return state.get("readiness_score", 0) >= AUTO_BRIEF_READINESS_THRESHOLD


def is_done_message(text: str) -> bool:
    normalized = text.strip().lower()
    return any(phrase in normalized for phrase in DONE_PHRASES)


def should_summarise(state: "OnboardingState", text: str) -> bool:
    """Explicit finish request or readiness met with brief intent."""
    normalized = text.strip().lower()
    brief_intent = any(
        p in normalized
        for p in ("generate my brief", "create the brief", "prepare my brief", "finish", "i'm done", "im done")
    )
    if is_done_message(text):
        return True
    if state.get("requirements_complete") and brief_intent:
        return True
    if state.get("requirements_complete") and state.get("readiness_score", 0) >= 0.85:
        if brief_intent or normalized in ("yes", "yes please", "go ahead", "proceed"):
            return True
    return False


def route_after_greeting(state: OnboardingState) -> str:
    return "consent"


def route_after_consent(state: OnboardingState) -> str:
    if state.get("consent_given"):
        return "identity"
    return "consent"


def route_after_identity(state: OnboardingState) -> str:
    if state.get("client_name"):
        return "requirements"
    return "identity"


def route_after_requirements(state: OnboardingState) -> str:
    last_user = _last_user_message(state)
    if last_user and is_done_message(last_user):
        return "summarise"
    if state.get("file_context"):
        return "clarify"
    return "requirements"


def route_after_clarify(state: OnboardingState) -> str:
    last_user = _last_user_message(state)
    if last_user and is_done_message(last_user):
        return "summarise"
    return "requirements"


def _last_user_message(state: OnboardingState) -> str | None:
    for msg in reversed(state.get("messages", [])):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return None
