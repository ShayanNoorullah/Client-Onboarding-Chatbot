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

MISSING_FIELD_CHIPS: dict[str, str] = {
    "project_type": "Website",
    "audience": "Small business owners",
    "features": "User login and dashboard",
    "timeline": "8 weeks",
    "budget": "$10k–$25k",
    "integrations": "No integrations needed",
    "design_preferences": "Modern and minimal",
}

PROJECT_TYPE_ALIASES: dict[str, str] = {
    "mobile app": "mobile_app_development",
    "mobile apps": "mobile_app_development",
    "mobile application": "mobile_app_development",
    "mobile applications": "mobile_app_development",
    "ios": "mobile_app_development",
    "android": "mobile_app_development",
    "website": "website_development",
    "web site": "website_development",
    "web development": "website_development",
    "software integration": "software_integration",
    "integration": "software_integration",
    "api integration": "software_integration",
    "consulting": "consulting",
    "mortgage website": "mortgage_website_development",
    "mortgage": "mortgage_website_development",
    "lending": "mortgage_website_development",
}

INITIAL_PROJECT_SUGGESTIONS = [
    "Website",
    "Mobile App",
    "Software Integration",
    "Consulting",
    "Mortgage / Lending",
]

PROJECT_TYPE_SUGGESTIONS: dict[str, list[str]] = {
    "mobile_app_development": [
        "iOS",
        "Android",
        "Both platforms",
        "8 weeks",
        "No integrations",
    ],
    "website_development": [
        "Corporate site",
        "E-commerce",
        "Lead generation",
        "8 weeks",
    ],
    "software_integration": [
        "CRM integration",
        "API development",
        "Legacy modernization",
        "8 weeks",
    ],
    "consulting": [
        "Project scoping",
        "Technical audit",
        "8 weeks",
    ],
    "mortgage_website_development": [
        "Loan application forms",
        "Mortgage calculators",
        "CRM / LOS integration",
        "8 weeks",
    ],
}

STAGE_SUGGESTIONS: dict[str, list[str]] = {
    "consent": ["I agree"],
    "identity": [],
    "requirements": INITIAL_PROJECT_SUGGESTIONS,
    "clarify": [
        "That looks good",
        "I have more files to upload",
    ],
    "summarise": [],
}


def uses_slm(stage: str) -> bool:
    return stage in SLM_RAG_STAGES


def uses_rules(stage: str) -> bool:
    return stage in RULE_BASED_STAGES


def normalize_project_type(user_message: str) -> str | None:
    """Map user chip or free text to a normalized project type key."""
    normalized = user_message.strip().lower()
    if not normalized:
        return None

    if normalized in PROJECT_TYPE_ALIASES:
        return PROJECT_TYPE_ALIASES[normalized]

    for alias, project_type in PROJECT_TYPE_ALIASES.items():
        if alias in normalized or normalized in alias:
            return project_type

    return None


def build_rag_query(user_message: str, project_type: str | None = None) -> str:
    """Formulate a retrieval query that targets the correct KB sections."""
    if project_type:
        label = project_type.replace("_", " ")
        return f"ATI services for {label}: {user_message}"
    detected = normalize_project_type(user_message)
    if detected:
        label = detected.replace("_", " ")
        return f"ATI services for {label}: {user_message}"
    return f"ATI services: {user_message}"


def get_suggestions(
    stage: str,
    client_name: str | None = None,
    project_type: str | None = None,
    requirements_complete: bool = False,
    missing_fields: list[str] | None = None,
) -> list[str]:
    if stage == "consent":
        return ["I agree", "Yes, I consent", "Tell me more about privacy"]
    if stage == "identity":
        return []

    if stage == "requirements":
        if requirements_complete:
            return ["Add more details"]
        if missing_fields:
            chips = []
            for field in missing_fields[:3]:
                if field in MISSING_FIELD_CHIPS:
                    chips.append(MISSING_FIELD_CHIPS[field])
            if chips:
                return chips
        if project_type and project_type in PROJECT_TYPE_SUGGESTIONS:
            return list(PROJECT_TYPE_SUGGESTIONS[project_type])
        return list(INITIAL_PROJECT_SUGGESTIONS)

    if stage == "clarify":
        if requirements_complete:
            return ["Add more details"]
        chips = list(STAGE_SUGGESTIONS.get("clarify", []))
        if missing_fields:
            for field in missing_fields[:2]:
                if field in MISSING_FIELD_CHIPS and MISSING_FIELD_CHIPS[field] not in chips:
                    chips.append(MISSING_FIELD_CHIPS[field])
        return chips

    return list(STAGE_SUGGESTIONS.get(stage, []))


def get_next_fallback_question(asked_count: int) -> str | None:
    if asked_count < len(FALLBACK_QUESTIONS):
        return FALLBACK_QUESTIONS[asked_count]
    return None


def extract_requirement_snippet(user_message: str, field: str) -> str:
    """Store a short snippet from user message for a requirement field."""
    return user_message.strip()[:500]
