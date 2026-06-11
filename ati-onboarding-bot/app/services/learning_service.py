import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.messages import HumanMessage

from app.config import settings
from app.llm.factory import get_chat_llm
from app.models.user_memory import UserMemory
from app.rag.embedder import embed_text

logger = logging.getLogger(__name__)

FACT_EXTRACT_PROMPT = """From this onboarding exchange, extract 0-2 durable facts about the client's preferences or business context.
Return ONLY valid JSON: {{"facts": ["fact one", "fact two"]}}
If nothing durable, return {{"facts": []}}

User: {user_message}
Assistant: {assistant_reply}
"""


async def get_user_memory_facts(user_id: str | None) -> list[str]:
    if not user_id:
        return []
    mem = await UserMemory.find_one(UserMemory.user_id == user_id)
    return list(mem.facts)[-10:] if mem else []


async def get_user_memory_context(user_id: str | None) -> dict:
    """Facts, project history, and formatted strings for prompts."""
    if not user_id:
        return {"facts": [], "project_history": [], "history_text": ""}
    mem = await UserMemory.find_one(UserMemory.user_id == user_id)
    if not mem:
        return {"facts": [], "project_history": [], "history_text": ""}
    history = list(mem.project_history)[-5:]
    lines = []
    for entry in history:
        pt = entry.get("project_type", "project")
        summary = entry.get("summary", "")[:120]
        lines.append(f"- {pt}: {summary}")
    return {
        "facts": list(mem.facts)[-10:],
        "project_history": history,
        "history_text": "\n".join(lines) if lines else "",
    }


async def extract_and_store_facts(
    user_id: str | None,
    user_message: str,
    assistant_reply: str,
) -> None:
    if not user_id or not user_message.strip():
        return
    try:
        llm = get_chat_llm(temperature=0.1)
        prompt = FACT_EXTRACT_PROMPT.format(
            user_message=user_message[:500],
            assistant_reply=assistant_reply[:500],
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        text = str(content).strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        facts = data.get("facts", [])
        if not facts:
            return
        mem = await UserMemory.find_one(UserMemory.user_id == user_id)
        if not mem:
            mem = UserMemory(user_id=user_id)
        for fact in facts[:2]:
            if fact and fact not in mem.facts:
                mem.facts.append(str(fact)[:300])
        mem.facts = mem.facts[-20:]
        mem.updated_at = datetime.now(timezone.utc)
        if mem.id:
            await mem.save()
        else:
            await mem.insert()
    except Exception:
        logger.exception("Failed to extract user memory facts")


async def learn_from_completed_session(state: dict) -> None:
    """Embed session insights and append anonymized global patterns."""
    user_id = state.get("user_id")
    client_name = state.get("client_name")
    workspace_slug = state.get("workspace_slug")
    collected = state.get("collected_requirements", {})
    requirements = state.get("requirements", {})

    if user_id:
        mem = await UserMemory.find_one(UserMemory.user_id == user_id)
        if not mem:
            mem = UserMemory(user_id=user_id)
        summary = requirements.get("project_summary", "")
        if summary:
            entry = {
                "ref_id": state.get("ref_id"),
                "project_type": collected.get("project_type"),
                "summary": summary[:500],
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
            mem.project_history.append(entry)
            mem.project_history = mem.project_history[-10:]
            fact = f"Completed project: {collected.get('project_type', 'unknown')} — {summary[:120]}"
            if fact not in mem.facts:
                mem.facts.append(fact)
            mem.facts = mem.facts[-20:]
            mem.updated_at = datetime.now(timezone.utc)
            if mem.id:
                await mem.save()
            else:
                await mem.insert()

        if client_name:
            memory_text = (
                f"User project history. Type: {collected.get('project_type')}. "
                f"Audience: {collected.get('audience')}. "
                f"Summary: {summary[:800]}"
            )
            memory_dir = settings.client_folder(client_name) / "_user_memory" / "vectors"
            embed_text(
                memory_text,
                f"user_memory_{user_id[:8]}",
                memory_dir,
                metadata={"user_id": user_id, "ref_id": state.get("ref_id")},
            )

    if workspace_slug and client_name:
        project_dir = settings.project_folder(client_name, workspace_slug)
        proj_text = json.dumps({"collected": collected, "summary": requirements}, indent=2)[:3000]
        embed_text(
            proj_text,
            f"project_{workspace_slug}",
            project_dir / "vectors",
            metadata={"workspace": workspace_slug},
        )

    _append_global_pattern(collected, requirements)
    from app.services.kb_reindex import reindex_learned_patterns

    reindex_learned_patterns()


def _append_global_pattern(collected: dict, requirements: dict) -> None:
    patterns_file = settings.ATI_KB_ROOT / "learned_patterns.txt"
    patterns_file.parent.mkdir(parents=True, exist_ok=True)
    pt = collected.get("project_type", "unknown")
    audience = collected.get("audience", "unspecified")[:80]
    services = requirements.get("recommended_services", [])
    if isinstance(services, list):
        services_str = ", ".join(str(s) for s in services[:3])
    else:
        services_str = str(services)
    line = (
        f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d')}] "
        f"project_type={pt}; audience={audience}; services={services_str}\n"
    )
    try:
        with patterns_file.open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        logger.exception("Failed to append learned pattern")
