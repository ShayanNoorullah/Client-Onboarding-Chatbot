from app.agent.routing import (
    can_request_manual_brief,
    is_ready_for_auto_brief,
    should_summarise,
    should_summarise_manual,
)
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


def test_should_summarise_manual_flag():
    state = default_state()
    state["manual_brief_requested"] = True
    assert should_summarise_manual(state) is True
    assert should_summarise(state, "hello") is True


def test_can_request_manual_brief():
    state = default_state()
    state["consent_given"] = True
    state["client_name"] = "Test_User"
    state["stage"] = "requirements"
    assert can_request_manual_brief(state) is True

    state["done"] = True
    assert can_request_manual_brief(state) is False


def test_is_ready_requires_slm_and_turns():
    state = default_state()
    state["requirements_complete"] = True
    state["readiness_score"] = 0.9
    state["slm_readiness_complete"] = False
    state["requirements_turn_count"] = 6
    assert is_ready_for_auto_brief(state) is False


def test_is_ready_when_all_gates_pass():
    state = default_state()
    state["requirements_complete"] = True
    state["readiness_score"] = 0.9
    state["slm_readiness_complete"] = True
    state["requirements_turn_count"] = 5
    assert is_ready_for_auto_brief(state) is True


def test_is_not_ready_with_few_turns():
    state = default_state()
    state["requirements_complete"] = True
    state["readiness_score"] = 0.9
    state["slm_readiness_complete"] = True
    state["requirements_turn_count"] = 2
    assert is_ready_for_auto_brief(state) is False


def test_auto_brief_when_ready_without_done_phrase():
    state = default_state()
    state["requirements_complete"] = True
    state["slm_readiness_complete"] = True
    state["readiness_score"] = 0.9
    state["requirements_turn_count"] = 6
    assert should_summarise(state, "Lead generation forms") is False
    assert is_ready_for_auto_brief(state) is True
