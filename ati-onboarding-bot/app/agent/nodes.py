import json
import logging
import re
from datetime import datetime, timezone

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agent.prompts import (
    CONSENT_MESSAGE,
    SUMMARY_EXTRACTION_PROMPT,
    build_slm_prompt,
)
from app.agent.state import OnboardingState
from app.agent.task_router import (
    FALLBACK_QUESTIONS,
    REQUIREMENT_FIELDS,
    get_next_fallback_question,
)
from app.config import settings
from app.llm.factory import get_chat_llm
from app.rag.retriever import query_combined_rag
from app.storage.encryptor import encrypt_log
from app.storage.file_manager import (
    create_client_workspace,
    get_conversation_log_path,
)
from app.storage.summary_writer import write_summary

logger = logging.getLogger(__name__)


def _append_message(state: OnboardingState, role: str, content: str) -> None:
    state["messages"].append({"role": role, "content": content})


def _get_rag_context(state: OnboardingState, query: str = "") -> str:
    if not query:
        for msg in reversed(state.get("messages", [])):
            if msg.get("role") == "user":
                query = msg.get("content", "")
                break
    if not query:
        query = "ATI services and privacy policy"
    try:
        return query_combined_rag(query, state.get("client_name"))
    except Exception:
        logger.exception("RAG query failed")
        return ""


def _update_collected_requirements(state: OnboardingState, user_message: str) -> None:
    collected = state.setdefault("collected_requirements", {})
    asked = state.get("requirements_asked", 0)
    if asked < len(REQUIREMENT_FIELDS):
        field = REQUIREMENT_FIELDS[asked]
        collected[field] = user_message.strip()[:500]
    state["requirements_asked"] = asked + 1


def _invoke_llm(state: OnboardingState, user_input: str | None = None) -> str:
    rag_context = _get_rag_context(state, user_input or "")
    system = build_slm_prompt(
        client_name=state.get("client_name") or "Not yet provided",
        stage=state.get("stage", "requirements"),
        assets_count=len(state.get("assets", [])),
        rag_context=rag_context,
        collected_requirements=state.get("collected_requirements", {}),
    )

    lc_messages = [SystemMessage(content=system)]
    for msg in state.get("messages", [])[-8:]:
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
        return str(content)
    except Exception as e:
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


def greeting_node(state: OnboardingState) -> OnboardingState:
    state["stage"] = "greeting"
    reply = CONSENT_MESSAGE.format(privacy_url=settings.ATI_PRIVACY_URL)
    state["pending_reply"] = reply
    _append_message(state, "assistant", reply)
    state["stage"] = "consent"
    return state


def consent_node(state: OnboardingState) -> OnboardingState:
    state["stage"] = "consent"
    last_user = _last_user_text(state)

    if last_user and _is_consent(last_user):
        state["consent_given"] = True
        state["consent_ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        reply = "Thank you! What is your full name?"
        state["pending_reply"] = reply
        _append_message(state, "assistant", reply)
        state["stage"] = "identity"
    elif last_user:
        reply = (
            "I need your consent before we can continue. "
            f"Please review our privacy policy at {settings.ATI_PRIVACY_URL} "
            'and type "I agree" to proceed.'
        )
        state["pending_reply"] = reply
        _append_message(state, "assistant", reply)
    else:
        reply = CONSENT_MESSAGE.format(privacy_url=settings.ATI_PRIVACY_URL)
        state["pending_reply"] = reply

    return state


def identity_node(state: OnboardingState) -> OnboardingState:
    state["stage"] = "identity"
    last_user = _last_user_text(state)

    if last_user and not state.get("client_name"):
        if _is_consent(last_user):
            reply = "Thank you! What is your full name?"
            state["pending_reply"] = reply
            _append_message(state, "assistant", reply)
            return state

        name = _extract_name(last_user)
        if name:
            state["client_name"] = name
            create_client_workspace(name)
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

    _update_collected_requirements(state, last_user)
    reply = _invoke_llm(state, last_user)
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

    reply = _invoke_llm(state, prompt)
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
    ref_id = f"{client_name}_{now}"
    state["ref_id"] = ref_id

    client_folder = create_client_workspace(client_name)
    write_summary(client_folder, state)

    log_data = {
        "session_id": state.get("session_id"),
        "client_name": client_name,
        "consent_ts": state.get("consent_ts"),
        "messages": state.get("messages"),
        "requirements": requirements,
        "assets": state.get("assets"),
        "ref_id": ref_id,
    }
    encrypt_log(log_data, get_conversation_log_path(client_folder))

    state["summary_written"] = True
    state["done"] = True

    reply = (
        "Let me prepare your project brief now...\n\n"
        f"Your brief is saved! An ATI advisor will review it and contact you within "
        f"3 business days. Your reference ID is {ref_id}.\n\n"
        f"Questions? Reach us at {settings.ATI_SUPPORT_EMAIL} or {settings.ATI_PHONE}."
    )
    state["pending_reply"] = reply
    _append_message(state, "assistant", reply)
    return state


def _last_user_text(state: OnboardingState) -> str | None:
    for msg in reversed(state.get("messages", [])):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return None


def _is_consent(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {"i agree", "agree", "yes i agree", "i consent", "consent"}


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
