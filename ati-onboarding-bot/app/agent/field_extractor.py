"""Semantic requirement field extraction."""
import json
import logging
import re
from langchain_core.messages import HumanMessage
from app.agent.task_router import REQUIREMENT_FIELDS, normalize_project_type
from app.agent.term_glossary import expand_terms
from app.llm.factory import get_chat_llm

logger = logging.getLogger(__name__)

FIELD_EXTRACTION_PROMPT = """Extract project requirement fields from the user message.
Return ONLY valid JSON with any of these keys that the user clearly provided:
project_type, audience, features, timeline, budget, integrations, design_preferences
Use empty object {{}} for keys not mentioned. Values should be concise (under 200 chars).

User message: {message}
Already collected: {collected}
"""


def _parse_json(text: str) -> dict:
    text = str(text).strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def extract_fields_from_message(user_message: str, collected: dict) -> dict:
    expanded = expand_terms(user_message)
    detected = normalize_project_type(expanded)
    updates: dict[str, str] = {}
    if detected and not collected.get("project_type"):
        updates["project_type"] = detected
    try:
        llm = get_chat_llm(temperature=0.1)
        prompt = FIELD_EXTRACTION_PROMPT.format(
            message=expanded[:800],
            collected=json.dumps(collected, indent=2),
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        data = _parse_json(str(content))
        for field in REQUIREMENT_FIELDS:
            val = data.get(field)
            if val and str(val).strip() and len(str(val).strip()) >= 2:
                if not collected.get(field) or field == "features":
                    updates[field] = str(val).strip()[:500]
    except Exception:
        logger.exception("Semantic field extraction failed")
    return updates


def merge_collected_requirements(state: dict, user_message: str) -> None:
    collected = state.setdefault("collected_requirements", {})
    updates = extract_fields_from_message(user_message, collected)
    for k, v in updates.items():
        collected[k] = v
    if not updates:
        asked = state.get("requirements_asked", 0)
        expanded = expand_terms(user_message)
        if asked < len(REQUIREMENT_FIELDS):
            field = REQUIREMENT_FIELDS[asked]
            if field == "project_type" and collected.get("project_type"):
                collected[field] = collected["project_type"]
            else:
                collected[field] = expanded.strip()[:500]
        state["requirements_asked"] = asked + 1
    else:
        state["requirements_asked"] = state.get("requirements_asked", 0) + 1
