"""SLM vs rule-based routing for onboarding stages."""

RULE_BASED_STAGES = {"greeting", "consent", "identity"}
SLM_RAG_STAGES = {"requirements", "clarify", "summarise"}
VISION_STAGES = {"asset_upload"}

FALLBACK_QUESTIONS = [
    "What type of project is this? (website, mobile app, software, integration)",
    "Who is your target audience?",
    "What key features or pages do you need?",
    "Do you have a timeline or launch date in mind?",
    "What is your approximate budget range?",
    "Any existing systems to integrate with?",
    "Any design references or brand guidelines to share?",
]

REQUIREMENT_FIELDS = [
    "project_type",
    "audience",
    "features",
    "timeline",
    "budget",
    "integrations",
    "design_preferences",
]

STAGE_SUGGESTIONS: dict[str, list[str]] = {
    "consent": ["I agree"],
    "identity": [],
    "requirements": [
        "Website",
        "Mobile App",
        "Software Integration",
        "Mortgage Website",
        "8 weeks",
        "No integrations",
        "I'm done",
    ],
    "clarify": [
        "That looks good",
        "I have more files to upload",
        "I'm done",
    ],
    "summarise": [],
}


def uses_slm(stage: str) -> bool:
    return stage in SLM_RAG_STAGES


def uses_rules(stage: str) -> bool:
    return stage in RULE_BASED_STAGES


def get_suggestions(stage: str, client_name: str | None = None) -> list[str]:
    suggestions = list(STAGE_SUGGESTIONS.get(stage, []))
    if stage == "requirements" and not client_name:
        return suggestions
    if stage == "identity":
        return []
    if stage == "consent":
        return ["I agree"]
    return suggestions


def get_next_fallback_question(asked_count: int) -> str | None:
    if asked_count < len(FALLBACK_QUESTIONS):
        return FALLBACK_QUESTIONS[asked_count]
    return None


def extract_requirement_snippet(user_message: str, field: str) -> str:
    """Store a short snippet from user message for a requirement field."""
    return user_message.strip()[:500]
