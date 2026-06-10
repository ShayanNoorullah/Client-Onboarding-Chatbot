from app.agent.routing import is_ready_for_auto_brief, should_summarise
from app.agent.state import default_state


def test_should_summarise_explicit_done():
    state = default_state()
    state["requirements_complete"] = False
    assert should_summarise(state, "I'm done") is True


def test_should_summarise_when_complete_and_intent():
    state = default_state()
    state["requirements_complete"] = True
    state["readiness_score"] = 0.9
    assert should_summarise(state, "Generate my brief") is True


def test_should_not_summarise_incomplete():
    state = default_state()
    state["requirements_complete"] = False
    assert should_summarise(state, "We need a website") is False


def test_is_ready_for_auto_brief():
    state = default_state()
    state["requirements_complete"] = True
    state["readiness_score"] = 0.9
    assert is_ready_for_auto_brief(state) is True


def test_is_not_ready_when_incomplete():
    state = default_state()
    state["requirements_complete"] = False
    state["readiness_score"] = 0.9
    assert is_ready_for_auto_brief(state) is False


def test_auto_brief_when_ready_without_done_phrase():
    state = default_state()
    state["stage"] = "requirements"
    state["client_name"] = "Test_Client"
    state["requirements_complete"] = True
    state["readiness_score"] = 0.9
    state["collected_requirements"] = {
        "project_type": "website_development",
        "audience": "SMBs",
        "features": "Lead gen",
        "timeline": "8 weeks",
    }
    state["messages"] = [
        {"role": "assistant", "content": "What features?"},
        {"role": "user", "content": "Lead generation forms"},
    ]
    assert is_ready_for_auto_brief(state) is True
    assert should_summarise(state, "Lead generation forms") is False
