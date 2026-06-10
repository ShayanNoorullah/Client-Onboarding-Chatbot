from pathlib import Path

from app.models.brief import Brief
from app.storage.file_manager import get_summary_path


async def persist_brief_to_mongo(state: dict) -> str | None:
    """Save completed brief to MongoDB. Returns brief_id."""
    if state.get("brief_id"):
        return state["brief_id"]
    if not state.get("done") or not state.get("user_id"):
        return None

    client_name = state.get("client_name", "Unknown")
    ref_id = state.get("ref_id", "unknown")
    summary_path = get_summary_path(client_name)
    markdown = ""
    if summary_path.exists():
        markdown = summary_path.read_text(encoding="utf-8")

    reqs = state.get("requirements", {})
    brief = Brief(
        user_id=state["user_id"],
        session_id=state.get("session_id", ""),
        ref_id=ref_id,
        client_name=client_name,
        markdown=markdown,
        recommended_services=reqs.get("recommended_services", [])
        if isinstance(reqs.get("recommended_services"), list)
        else [],
        file_path=str(summary_path) if summary_path.exists() else None,
    )
    await brief.insert()
    return str(brief.id)
