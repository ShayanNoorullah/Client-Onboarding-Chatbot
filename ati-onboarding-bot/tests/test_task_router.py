from app.agent.task_router import (
    FALLBACK_QUESTIONS,
    build_rag_query,
    get_next_fallback_question,
    get_suggestions,
    normalize_project_type,
    uses_rules,
    uses_slm,
)


def test_uses_rules():
    assert uses_rules("consent")
    assert uses_rules("identity")
    assert not uses_rules("requirements")


def test_uses_slm():
    assert uses_slm("requirements")
    assert uses_slm("summarise")
    assert not uses_slm("consent")


def test_get_suggestions_consent():
    suggestions = get_suggestions("consent")
    assert "I agree" in suggestions
    assert "Yes, I consent" in suggestions


def test_get_suggestions_requirements_initial():
    s = get_suggestions("requirements", "Test_Client")
    assert "Website" in s
    assert "Mobile App" in s
    assert "Mortgage Website" not in s
    assert "I'm done" not in s


def test_get_suggestions_requirements_missing_fields():
    s = get_suggestions(
        "requirements", "Test_Client", "mobile_app_development", False, ["timeline", "budget"]
    )
    assert "8 weeks" in s
    assert "I'm done" not in s


def test_get_suggestions_requirements_complete():
    s = get_suggestions("requirements", "Test_Client", "mobile_app_development", True)
    assert s == ["Add more details"]
    assert "I'm done" not in s
    assert "Generate my brief" not in s


def test_get_suggestions_requirements_mobile():
    s = get_suggestions("requirements", "Test_Client", "mobile_app_development")
    assert "iOS" in s
    assert "Android" in s
    assert "Mortgage Website" not in s
    assert "I'm done" not in s


def test_normalize_project_type():
    assert normalize_project_type("Mobile App") == "mobile_app_development"
    assert normalize_project_type("Website") == "website_development"
    assert normalize_project_type("Software Integration") == "software_integration"
    assert normalize_project_type("Mortgage / Lending") == "mortgage_website_development"
    assert normalize_project_type("random text") is None


def test_build_rag_query():
    assert "mobile app development" in build_rag_query("Mobile App").lower()
    assert "mobile app development" in build_rag_query(
        "push notifications", "mobile_app_development"
    ).lower()


def test_fallback_questions():
    assert get_next_fallback_question(0) == FALLBACK_QUESTIONS[0]
    assert get_next_fallback_question(99) is None
