import json
import logging
import re
from datetime import datetime, timezone

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agent.prompts import (
    COMPLETION_EVAL_PROMPT,
    CONSENT_SLM_PROMPT,
    SUMMARY_EXTRACTION_PROMPT,
    build_slm_prompt,
)
from app.agent.state import OnboardingState
from app.agent.routing import MIN_FIELD_VALUE_LEN
from app.agent.task_router import (
    FALLBACK_QUESTIONS,
    REQUIREMENT_FIELDS,
    build_rag_query,
    get_next_fallback_question,
    normalize_project_type,
)
from app.agent.term_glossary import expand_terms
from app.agent.field_extractor import merge_collected_requirements
from app.agent.session_memory import maybe_update_session_summary
from app.agent.reflect_helpers import reflect_on_brief
from app.services.agent_metrics import timed
from app.config import settings
from app.llm.factory import get_chat_llm
from app.rag.retriever import query_combined_rag
from app.storage.encryptor import encrypt_log
from app.storage.file_manager import (
    create_project_workspace,
    get_project_folder_from_state,
    write_conversation_log,
)
from app.storage.summary_writer import write_summary

logger = logging.getLogger(__name__)


def _append_message(state: OnboardingState, role: str, content: str) -> None:
    state["messages"].append({"role": role, "content": content})


def _format_project_history(state: OnboardingState) -> str:
    history = state.get("project_history") or []
    if not history:
        return ""
    lines = []
    for entry in history:
        pt = entry.get("project_type", "project")
        summary = str(entry.get("summary", ""))[:120]
        lines.append(f"- {pt}: {summary}")
    return "\n".join(lines)


def _get_rag_context(state: OnboardingState, query: str = "") -> str:
    if not query:
        for msg in reversed(state.get("messages", [])):
            if msg.get("role") == "user":
                query = msg.get("content", "")
                break
    if not query:
        query = "ATI services and privacy policy"

    project_type = state.get("collected_requirements", {}).get("project_type")
    rag_query = build_rag_query(query, project_type)
    try:
        sid = state.get("session_id", "")
        stage = state.get("stage", "")
        with timed("rag", sid, stage):
            return query_combined_rag(
                rag_query,
                state.get("client_name"),
                state.get("workspace_slug"),
                user_id=state.get("user_id"),
            )
    except Exception:
        logger.exception("RAG query failed")
        return ""


def _update_collected_requirements(state: OnboardingState, user_message: str) -> None:
    collected = state.setdefault("collected_requirements", {})
    asked = state.get("requirements_asked", 0)
    expanded = expand_terms(user_message)

    detected_type = normalize_project_type(user_message)
    if detected_type and not collected.get("project_type"):
        collected["project_type"] = detected_type

    if asked < len(REQUIREMENT_FIELDS):
        field = REQUIREMENT_FIELDS[asked]
        if field == "project_type" and collected.get("project_type"):
            collected[field] = collected["project_type"]
        else:
            collected[field] = expanded.strip()[:500]
    state["requirements_asked"] = asked + 1


def _invoke_llm(state: OnboardingState, user_input: str | None = None) -> str:
    rag_context = _get_rag_context(state, user_input or "")
    system = build_slm_prompt(
        client_name=state.get("client_name") or "Not yet provided",
        stage=state.get("stage", "requirements"),
        assets_count=len(state.get("assets", [])),
        rag_context=rag_context,
        collected_requirements=state.get("collected_requirements", {}),
        user_memory_facts=state.get("user_memory_facts"),
        project_history_text=_format_project_history(state),
        session_summary=state.get("session_summary", ""),
        learned_constraints=state.get("learned_constraints", "None yet"),
        slm_template=state.get("slm_prompt_template"),
    )
    state["last_rag_context"] = rag_context

    lc_messages = [SystemMessage(content=system)]
    for msg in state.get("messages", [])[-6:]:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_messages.append(AIMessage(content=msg["content"]))

    if user_input:
        lc_messages.append(HumanMessage(content=user_input))

    try:
        llm = get_chat_llm(temperature=0.3)
        response = llm.invoke(lc_messages)
        content = response.content
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        state["used_fallback"] = False
        return str(content)
    except Exception as e:
        state["used_fallback"] = True
        logger.exception("Ollama LLM call failed")
        asked = state.get("requirements_asked", 0)
        fallback = get_next_fallback_question(asked)
        if fallback:
            return (
                f"I'm using a backup question while the AI warms up ({type(e).__name__}).\n\n"
                f"{fallback}"
            )
        return (
            "I'm having trouble reaching Ollama right now. "
            "Please ensure Ollama is running (`ollama serve`) and models are pulled. "
            f"Contact ATI at {settings.ATI_SUPPORT_EMAIL} if you need help."
        )




def build_llm_messages(state: OnboardingState, user_input: str | None = None) -> list:
    rag_context = _get_rag_context(state, user_input or "")
    system = build_slm_prompt(
        client_name=state.get("client_name") or "Not yet provided",
        stage=state.get("stage", "requirements"),
        assets_count=len(state.get("assets", [])),
        rag_context=rag_context,
        collected_requirements=state.get("collected_requirements", {}),
        user_memory_facts=state.get("user_memory_facts"),
        project_history_text=_format_project_history(state),
        session_summary=state.get("session_summary", ""),
        learned_constraints=state.get("learned_constraints", "None yet"),
        slm_template=state.get("slm_prompt_template"),
    )
    state["last_rag_context"] = rag_context
    lc_messages = [SystemMessage(content=system)]
    for msg in state.get("messages", [])[-6:]:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_messages.append(AIMessage(content=msg["content"]))
    if user_input:
        lc_messages.append(HumanMessage(content=user_input))
    return lc_messages


def stream_llm_reply(state: OnboardingState, user_input: str):
    from app.llm.factory import stream_chat_llm
    for chunk in stream_chat_llm(build_llm_messages(state, user_input), temperature=0.3):
        yield chunk

def _parse_json_response(text: str) -> dict:
    text = str(text).strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _classify_consent(state: OnboardingState, user_message: str = "") -> tuple[bool, str]:
    rag = _get_rag_context(state, "ATI privacy policy data collection")
    prompt = CONSENT_SLM_PROMPT.format(
        rag_context=rag[:1200] or "ATI collects name, project details, files for brief preparation only.",
        support_email=settings.ATI_SUPPORT_EMAIL,
        privacy_url=settings.ATI_PRIVACY_URL,
        user_message=user_message or "No message yet — give initial consent explanation.",
    )
    try:
        llm = get_chat_llm(temperature=0.2)
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        data = _parse_json_response(str(content))
        if data.get("reply"):
            return bool(data.get("consent_detected")), str(data["reply"])
    except Exception:
        logger.exception("Consent SLM failed")
    privacy_link = settings.ATI_PRIVACY_URL
    if not user_message:
        return False, (
            "Hello! I'm the Client Onboarding Agent. Before we begin, Awesome Technologies Inc. "
            f"collects the information you share to prepare your project brief. "
            f"Review our privacy policy at {privacy_link} and let me know when you're "
            "comfortable proceeding."
        )
    return False, (
        "I wasn't able to confirm your consent just now. Please review our privacy policy at "
        f"{privacy_link} and reply in your own words when you're comfortable continuing."
    )


def _field_substantive(value: str | None) -> bool:
    return bool(value and len(str(value).strip()) >= MIN_FIELD_VALUE_LEN)


def _rule_based_readiness(collected: dict) -> tuple[bool, float, list[str]]:
    """Fast rule check: project_type + 5 other substantive fields."""
    missing = []
    for f in REQUIREMENT_FIELDS:
        if not _field_substantive(collected.get(f)):
            missing.append(f)
    filled = len(REQUIREMENT_FIELDS) - len(missing)
    has_type = _field_substantive(collected.get("project_type"))
    complete = has_type and filled >= 6
    score = min(filled / len(REQUIREMENT_FIELDS), 1.0) if has_type else filled / len(REQUIREMENT_FIELDS) * 0.5
    if complete:
        score = max(score, 0.85)
    return complete, score, missing


def _evaluate_readiness(state: OnboardingState) -> None:
    collected = state.get("collected_requirements", {})
    rule_complete, rule_score, rule_missing = _rule_based_readiness(collected)

    conversation = "\n".join(
        f"{m['role']}: {m['content']}" for m in state.get("messages", [])[-10:]
    )
    prompt = COMPLETION_EVAL_PROMPT.format(
        collected=json.dumps(collected, indent=2),
        conversation=conversation[:2000],
    )
    if len(rule_missing) > 2 and not rule_complete:
        state["slm_readiness_complete"] = False
        state["requirements_complete"] = False
        state["readiness_score"] = rule_score
        state["missing_fields"] = rule_missing
        return
    try:
        llm = get_chat_llm(temperature=0.1)
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        data = _parse_json_response(str(content))
        slm_complete = bool(data.get("complete", False))
        slm_score = float(data.get("score", 0.0))
        slm_missing = data.get("missing", []) or []
        state["slm_readiness_complete"] = slm_complete
        state["requirements_complete"] = rule_complete and slm_complete
        state["readiness_score"] = max(rule_score, slm_score)
        state["missing_fields"] = slm_missing if slm_missing else rule_missing
    except Exception:
        logger.exception("Readiness evaluation failed")
        state["slm_readiness_complete"] = False
        state["requirements_complete"] = False
        state["readiness_score"] = rule_score
        state["missing_fields"] = rule_missing


def _ensure_project_workspace(state: OnboardingState) -> None:
    if state.get("workspace_slug") or not state.get("client_name"):
        return
    _, slug = create_project_workspace(state["client_name"], state.get("session_id", ""))
    state["workspace_slug"] = slug


MODAL_CONSENT_PHRASE = "i agree"


def is_modal_consent_phrase(text: str) -> bool:
    return text.strip().lower() == MODAL_CONSENT_PHRASE


def record_modal_consent(state: OnboardingState) -> OnboardingState:
    """Record consent from the privacy dialog (exact phrase: I agree)."""
    state["consent_given"] = True
    state["consent_ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    state["consent_pending_slm"] = False
    state["consent_prompt_sent"] = True

    if state.get("client_name"):
        _ensure_project_workspace(state)
        display = state["client_name"].replace("_", " ")
        reply = (
            f"Thank you, {display}! Your profile is linked to this project.\n\n"
            "What kind of project can we help you with today?"
        )
        state["stage"] = "requirements"
    else:
        state["stage"] = "identity"
        reply = "Thank you! Please confirm your full name for this project."

    state["pending_reply"] = reply
    state["messages"] = [{"role": "assistant", "content": reply}]
    return state


def _after_consent(state: OnboardingState, reply: str) -> None:
    state["consent_given"] = True
    state["consent_ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if state.get("client_name"):
        _ensure_project_workspace(state)
        display = state["client_name"].replace("_", " ")
        reply = (
            f"Thank you, {display}! Your profile is linked to this project.\n\n"
            "What kind of project can we help you with today?"
        )
        state["stage"] = "requirements"
    else:
        state["stage"] = "identity"
        reply = reply or "Thank you! Please confirm your full name for this project."
    state["pending_reply"] = reply
    _append_message(state, "assistant", reply)


CONSENT_PLACEHOLDER = (
    "Welcome! I'm preparing a brief privacy notice for you — one moment..."
)


def greeting_node(state: OnboardingState) -> OnboardingState:
    """Initialize session — consent is collected via the UI dialog, not chat."""
    state["stage"] = "consent"
    state["consent_prompt_sent"] = True
    state["consent_pending_slm"] = False
    state["pending_reply"] = ""
    return state


def generate_slm_consent_intro(state: OnboardingState) -> OnboardingState:
    """Replace placeholder with SLM-personalised consent message."""
    _, reply = _classify_consent(state, "")
    if state.get("messages") and state["messages"][-1].get("content") == CONSENT_PLACEHOLDER:
        state["messages"][-1]["content"] = reply
    else:
        _append_message(state, "assistant", reply)
    state["pending_reply"] = reply
    state["consent_pending_slm"] = False
    return state


def consent_node(state: OnboardingState) -> OnboardingState:
    state["stage"] = "consent"
    if state.get("consent_given"):
        return state

    last_user = _last_user_text(state)
    if not last_user:
        return state

    if is_modal_consent_phrase(last_user):
        return record_modal_consent(state)

    reply = (
        'Please complete the privacy consent dialog and type "I agree" to continue.'
    )
    state["pending_reply"] = reply
    _append_message(state, "assistant", reply)
    return state


def identity_node(state: OnboardingState) -> OnboardingState:
    state["stage"] = "identity"
    last_user = _last_user_text(state)

    if state.get("client_name") and state.get("consent_given"):
        state["stage"] = "requirements"
        return state

    if last_user:
        name = _extract_name(last_user)
        if name:
            state["client_name"] = name
            _ensure_project_workspace(state)
            display_name = name.replace("_", " ")
            reply = (
                f"Got it, {display_name}! I'll use this name for your project workspace.\n\n"
                "What kind of project can we help you with today?"
            )
            state["pending_reply"] = reply
            _append_message(state, "assistant", reply)
            state["stage"] = "requirements"
        else:
            reply = "Could you please share your full name so I can set up your project workspace?"
            state["pending_reply"] = reply
            _append_message(state, "assistant", reply)

    return state


def requirements_node(state: OnboardingState) -> OnboardingState:
    state["stage"] = "requirements"
    last_user = _last_user_text(state)

    if not last_user:
        return state

    if _contains_financial_data(last_user):
        reply = (
            "For your security, please do not share credit card numbers, bank details, "
            "SSNs, or passwords. They are not needed for this onboarding process. "
            "Let's continue with your project requirements instead."
        )
        state["pending_reply"] = reply
        _append_message(state, "assistant", reply)
        return state

    merge_collected_requirements(state, last_user)
    maybe_update_session_summary(state)
    state["requirements_turn_count"] = state.get("requirements_turn_count", 0) + 1
    reply = _invoke_llm(state, expand_terms(last_user))
    _evaluate_readiness(state)
    state["pending_reply"] = reply
    _append_message(state, "assistant", reply)
    state["file_context"] = ""
    return state


def clarify_node(state: OnboardingState) -> OnboardingState:
    state["stage"] = "clarify"
    last_user = _last_user_text(state)

    file_ctx = state.get("file_context", "")
    prompt = last_user or "The client just uploaded a file."
    if file_ctx:
        prompt = f"{prompt}\n\n[Uploaded file context]: {file_ctx}"

    if last_user:
        merge_collected_requirements(state, last_user)
        maybe_update_session_summary(state)
    state["requirements_turn_count"] = state.get("requirements_turn_count", 0) + 1
    reply = _invoke_llm(state, expand_terms(prompt))
    _evaluate_readiness(state)
    state["pending_reply"] = reply
    _append_message(state, "assistant", reply)
    state["file_context"] = ""
    return state


def summarise_node(state: OnboardingState) -> OnboardingState:
    state["stage"] = "summarise"

    conversation = "\n".join(
        f"{m['role']}: {m['content']}" for m in state.get("messages", [])
    )
    rag_context = _get_rag_context(state, "ATI services for this project")

    try:
        llm = get_chat_llm(temperature=0.1)
        extraction_prompt = SUMMARY_EXTRACTION_PROMPT.format(conversation=conversation)
        if rag_context:
            extraction_prompt += f"\n\nATI RAG context:\n{rag_context[:1500]}"
        extraction_response = llm.invoke([HumanMessage(content=extraction_prompt)])
        text = extraction_response.content
        if isinstance(text, list):
            text = " ".join(str(c) for c in text)
        text = str(text).strip()
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        requirements = json.loads(text)
    except Exception:
        logger.exception("Summary extraction failed, using fallback")
        collected = state.get("collected_requirements", {})
        requirements = {
            "project_summary": "Project requirements gathered during onboarding session.",
            "items": [f"{k}: {v}" for k, v in collected.items()] or ["See conversation log."],
            "contact_preference": "Not specified",
            "recommended_services": _extract_services_from_rag(rag_context),
        }

    state["requirements"] = requirements

    client_name = state.get("client_name", "Unknown")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    is_update = bool(state.get("brief_id") or state.get("brief_update_pending") or state.get("summary_written"))
    version = state.get("brief_version", 1)
    if is_update:
        version = version + 1
        state["brief_version"] = version
        ref_id = state.get("ref_id") or f"{client_name}_{now}"
        if not ref_id.endswith(f"_v{version}"):
            ref_id = f"{ref_id}_v{version}"
    else:
        ref_id = f"{client_name}_{now}"
        state["brief_version"] = 1
    state["ref_id"] = ref_id

    _ensure_project_workspace(state)
    client_folder = get_project_folder_from_state(state)
    write_summary(client_folder, state)

    log_data = {
        "session_id": state.get("session_id"),
        "client_name": client_name,
        "consent_ts": state.get("consent_ts"),
        "messages": state.get("messages"),
        "requirements": requirements,
        "assets": state.get("assets"),
        "ref_id": ref_id,
        "brief_version": state.get("brief_version", 1),
    }
    log_path = write_conversation_log(client_folder, log_data)
    if settings.ENCRYPTION_KEY:
        try:
            encrypt_log(log_data, log_path)
        except Exception:
            logger.exception("Failed to write encrypted conversation log")

    reflection = reflect_on_brief(state)
    state["reflection"] = reflection
    state["summary_written"] = True
    state["done"] = True
    state["manual_brief_requested"] = False
    state["brief_update_pending"] = False
    state["auto_summarising"] = False

    if is_update:
        reply = (
            "I've updated your project brief with the latest information.\n\n"
            f"Your reference ID is {ref_id}. An ATI advisor will review the changes.\n\n"
            f"Questions? Reach us at {settings.ATI_SUPPORT_EMAIL} or {settings.ATI_PHONE}."
        )
    else:
        reply = (
            "Let me prepare your project brief now...\n\n"
            f"Your brief is saved! An ATI advisor will review it and contact you within "
            f"3 business days. Your reference ID is {ref_id}.\n\n"
            f"Questions? Reach us at {settings.ATI_SUPPORT_EMAIL} or {settings.ATI_PHONE}."
        )
    state["pending_reply"] = reply
    _append_message(state, "assistant", reply)
    return state




def proactive_clarify_after_upload(state: OnboardingState) -> OnboardingState:
    """Generate assistant reply after file upload without user message."""
    state["stage"] = "clarify"
    state["requirements_turn_count"] = state.get("requirements_turn_count", 0) + 1
    file_ctx = state.get("file_context", "")
    prompt = f"I just uploaded a project file. Please review it and tell me what you found.\n\n[Uploaded file context]: {file_ctx}"
    state["messages"].append({"role": "user", "content": "I uploaded a file for review."})
    reply = _invoke_llm(state, expand_terms(prompt))
    _evaluate_readiness(state)
    state["pending_reply"] = reply
    _append_message(state, "assistant", reply)
    state["file_context"] = ""
    return state


def _last_user_text(state: OnboardingState) -> str | None:
    for msg in reversed(state.get("messages", [])):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return None


def _extract_name(text: str) -> str | None:
    cleaned = text.strip()
    if len(cleaned) < 2:
        return None
    from app.storage.file_manager import sanitise_name
    return sanitise_name(cleaned)


def _contains_financial_data(text: str) -> bool:
    patterns = [
        r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        r"\bssn\b",
        r"\bsocial security\b",
        r"\bcredit card\b",
        r"\bbank account\b",
        r"\bpassword\b",
    ]
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)


def _extract_services_from_rag(rag_context: str) -> list[str]:
    services = []
    keywords = [
        "Mortgage Website Development",
        "Mortgage Website Design",
        "Custom Mortgage Development",
        "Mortgage Automation",
        "LOS Implementation",
        "CRM Integration",
        "Custom Software Development",
    ]
    for kw in keywords:
        if kw.lower() in rag_context.lower():
            services.append(kw)
    return services or ["To be matched by ATI advisor."]
