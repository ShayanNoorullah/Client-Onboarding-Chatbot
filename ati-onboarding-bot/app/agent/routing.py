from app.agent.state import OnboardingState

DONE_PHRASES = {
    "i'm done", "im done", "that's all", "thats all", "nothing else",
    "no more questions", "prepare my brief", "generate my brief",
    "i am done", "we're done", "were done", "all done", "finish up",
    "create the brief", "ready to go",
}

CONSENT_PHRASES = {"i agree", "agree", "yes i agree", "i consent", "consent"}


def is_consent_message(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in CONSENT_PHRASES or normalized.startswith("i agree")


def is_done_message(text: str) -> bool:
    normalized = text.strip().lower()
    return any(phrase in normalized for phrase in DONE_PHRASES)


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
