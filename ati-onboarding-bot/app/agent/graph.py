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
        if state.get("file_context"):
            return clarify_node(state)
        return requirements_node(state)
    if stage == "clarify":
        return clarify_node(state)
    if stage == "summarise":
        return summarise_node(state)

    return state


def process_message(state: OnboardingState, user_message: str) -> OnboardingState:
    """Process a user message — one stage per message, no chaining."""
    from app.agent.routing import is_consent_message, is_done_message

    state["messages"].append({"role": "user", "content": user_message})
    stage = state.get("stage", "greeting")

    if is_consent_message(user_message) and stage in ("greeting", "consent"):
        state["stage"] = "consent"
        return consent_node(state)

    if stage == "greeting":
        return greeting_node(state)
    if stage == "consent":
        return consent_node(state)
    if stage == "identity":
        return identity_node(state)
    if stage == "requirements":
        if is_done_message(user_message):
            return summarise_node(state)
        if state.get("file_context"):
            return clarify_node(state)
        return requirements_node(state)
    if stage == "clarify":
        if is_done_message(user_message):
            return summarise_node(state)
        return clarify_node(state)
    if stage == "summarise":
        return summarise_node(state)

    return state
