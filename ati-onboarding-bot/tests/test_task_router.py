from app.agent.task_router import (
    FALLBACK_QUESTIONS,
    get_next_fallback_question,
    get_suggestions,
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
    assert get_suggestions("consent") == ["I agree"]


def test_get_suggestions_requirements():
    s = get_suggestions("requirements", "Test_Client")
    assert "Website" in s
    assert "I'm done" in s


def test_fallback_questions():
    assert get_next_fallback_question(0) == FALLBACK_QUESTIONS[0]
    assert get_next_fallback_question(99) is None
