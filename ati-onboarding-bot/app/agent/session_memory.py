"""Rolling session summary for long conversations."""
import logging
from langchain_core.messages import HumanMessage
from app.llm.factory import get_chat_llm

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """Summarize this onboarding conversation in 4-6 bullet points.
Focus on: project type, goals, audience, features, timeline, budget, integrations, design.
Keep under 400 words.

{conversation}
"""


def maybe_update_session_summary(state: dict) -> None:
    turn_count = state.get("requirements_turn_count", 0)
    if turn_count < 4 or turn_count % 4 != 0:
        return
    messages = state.get("messages", [])
    if len(messages) < 10:
        return
    conversation = "\n".join(f"{m['role']}: {m['content']}" for m in messages[:-6])
    try:
        llm = get_chat_llm(temperature=0.1)
        response = llm.invoke([HumanMessage(content=SUMMARY_PROMPT.format(conversation=conversation[:3000]))])
        content = response.content
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        state["session_summary"] = str(content).strip()[:1200]
    except Exception:
        logger.exception("Session summary update failed")
