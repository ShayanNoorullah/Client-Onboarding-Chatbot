from app.agent.nodes import is_modal_consent_phrase, record_modal_consent
from app.agent.state import default_state


def test_is_modal_consent_phrase_accepts_exact_phrase():
    assert is_modal_consent_phrase("I agree")
    assert is_modal_consent_phrase("i agree")
    assert is_modal_consent_phrase("  I agree  ")


def test_is_modal_consent_phrase_rejects_other_replies():
    assert not is_modal_consent_phrase("yes")
    assert not is_modal_consent_phrase("it is ok")
    assert not is_modal_consent_phrase("I agree!")


def test_record_modal_consent_advances_to_identity():
    state = default_state()
    state["session_id"] = "sess-1"
    state["user_id"] = "user-1"
    state = record_modal_consent(state)
    assert state["consent_given"] is True
    assert state["stage"] == "identity"
    assert state["messages"][-1]["role"] == "assistant"
    assert "full name" in state["messages"][-1]["content"].lower()
