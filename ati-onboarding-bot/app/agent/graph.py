from langgraph.graph import END, StateGraph

from app.agent.nodes import (
    clarify_node,
    consent_node,
    greeting_node,
    identity_node,
    requirements_node,
    summarise_node,
)
from app.agent.routing import (
    route_after_clarify,
    route_after_consent,
    route_after_greeting,
    route_after_identity,
    route_after_requirements,
)
from app.agent.state import OnboardingState, default_state

graph = StateGraph(OnboardingState)

graph.add_node("greeting", greeting_node)
graph.add_node("consent", consent_node)
graph.add_node("identity", identity_node)
graph.add_node("requirements", requirements_node)
graph.add_node("clarify", clarify_node)
graph.add_node("summarise", summarise_node)

graph.set_entry_point("greeting")
graph.add_conditional_edges("greeting", route_after_greeting)
graph.add_conditional_edges("consent", route_after_consent)
graph.add_conditional_edges("identity", route_after_identity)
graph.add_conditional_edges("requirements", route_after_requirements)
graph.add_conditional_edges("clarify", route_after_clarify)
graph.add_edge("summarise", END)

compiled_graph = graph.compile()


def _has_pending_context(state: OnboardingState) -> bool:
    return bool(state.get("file_context") or state.get("url_context"))


def run_agent_step(state: OnboardingState) -> OnboardingState:
    """Run one step of the agent based on current stage."""
    stage = state.get("stage", "greeting")

    if stage == "greeting":
        return greeting_node(state)
    if stage == "consent":
        return consent_node(state)
    if stage == "identity":
        return identity_node(state)
    if stage == "requirements":
        if _has_pending_context(state):
            return clarify_node(state)
        return requirements_node(state)
    if stage == "clarify":
        return clarify_node(state)
    if stage == "summarise":
        return summarise_node(state)

    return state


def _maybe_auto_summarise(state: OnboardingState) -> OnboardingState:
    from app.agent.routing import is_ready_for_auto_brief

    if not is_ready_for_auto_brief(state):
        return state
    if not state.get("brief_recap_shown"):
        collected = state.get("collected_requirements", {})
        recap_lines = [f"- {k}: {v}" for k, v in collected.items() if v]
        recap = "Here is what I have captured so far:\n" + "\n".join(recap_lines[:8])
        recap += "\n\nDoes this look right? You can add more details or say \"generate brief\" when ready."
        state["brief_recap_shown"] = True
        state["awaiting_brief_confirm"] = True
        state["pending_reply"] = recap
        _append_transition(state, recap)
        return state
    transition = "I have enough information — preparing your project brief now..."
    state["auto_summarising"] = True
    state["pending_reply"] = transition
    _append_transition(state, transition)
    return summarise_node(state)


def _append_transition(state: OnboardingState, text: str) -> None:
    state["messages"].append({"role": "assistant", "content": text})


def _reopen_completed_session(state: OnboardingState) -> None:
    """Allow the user to add more info and update an existing brief."""
    state["done"] = False
    state["brief_update_pending"] = True
    state["auto_summarising"] = False
    state["manual_brief_requested"] = False
    if state.get("file_context") or state.get("url_context"):
        state["stage"] = "clarify"
    else:
        state["stage"] = "requirements"
    note = (
        "Welcome back! I'll keep gathering details and can update your project brief "
        "when you're ready — use Generate Brief or keep chatting."
    )
    state["pending_reply"] = note
    _append_transition(state, note)


def process_message(state: OnboardingState, user_message: str) -> OnboardingState:
    """Process a user message — one stage per message, no chaining."""
    from app.agent.routing import should_summarise

    state["messages"].append({"role": "user", "content": user_message})
    stage = state.get("stage", "greeting")

    if state.get("done"):
        _reopen_completed_session(state)
        if _has_pending_context(state):
            state = clarify_node(state)
        else:
            state = requirements_node(state)
        return state

    if stage == "greeting":
        state["stage"] = "consent"
        return consent_node(state)
    if stage == "consent":
        return consent_node(state)
    if stage == "identity":
        return identity_node(state)
    if stage == "requirements":
        if should_summarise(state, user_message):
            return summarise_node(state)
        if _has_pending_context(state):
            state = clarify_node(state)
        else:
            state = requirements_node(state)
        return _maybe_auto_summarise(state)
    if stage == "clarify":
        if should_summarise(state, user_message):
            return summarise_node(state)
        state = clarify_node(state)
        return _maybe_auto_summarise(state)
    if stage == "summarise":
        return summarise_node(state)

    return state


def request_manual_brief(state: OnboardingState) -> OnboardingState:
    """Generate brief on user request, bypassing auto-readiness gates."""
    from app.agent.routing import can_request_manual_brief

    if not can_request_manual_brief(state):
        if not state.get("consent_given"):
            reply = "Please complete the privacy consent step before generating a brief."
        elif not state.get("client_name"):
            reply = "Please share your name first so I can set up your project workspace."
        else:
            reply = "Your brief is already complete. Send a message if you'd like to add more details."
        state["pending_reply"] = reply
        _append_transition(state, reply)
        return state

    state["manual_brief_requested"] = True
    transition = "Generating your project brief on your request..."
    state["pending_reply"] = transition
    _append_transition(state, transition)
    return summarise_node(state)
