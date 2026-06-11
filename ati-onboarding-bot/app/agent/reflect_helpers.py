"""Post-summarise brief reflection."""
import json
import logging
import re
from langchain_core.messages import HumanMessage
from app.llm.factory import get_chat_llm

logger = logging.getLogger(__name__)

REFLECTION_PROMPT = """Compare the generated brief requirements against collected fields and conversation.
Return ONLY valid JSON:
{{"gaps": ["list of missing or weak areas"], "ok": true/false, "note": "one sentence"}}

Collected: {collected}
Brief requirements: {requirements}
"""


def reflect_on_brief(state: dict) -> dict:
    try:
        llm = get_chat_llm(temperature=0.1)
        prompt = REFLECTION_PROMPT.format(
            collected=json.dumps(state.get("collected_requirements", {})),
            requirements=json.dumps(state.get("requirements", {}))[:2000],
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        text = str(content).strip()
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text)
    except Exception:
        logger.exception("Brief reflection failed")
        return {"gaps": [], "ok": True, "note": ""}
