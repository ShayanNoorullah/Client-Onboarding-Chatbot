from datetime import datetime, timezone

from app.models.brief import Brief
from app.models.user import User
from app.services.email_service import send_templated_email
from app.storage.file_manager import get_summary_path


async def persist_brief_to_mongo(state: dict) -> str | None:
    """Save or update completed brief in MongoDB. Returns brief_id."""
    if not state.get("done") or not state.get("user_id"):
        return None

    client_name = state.get("client_name", "Unknown")
    ref_id = state.get("ref_id", "unknown")
    summary_path = get_summary_path(client_name, state.get("workspace_slug"))
    markdown = ""
    if summary_path.exists():
        markdown = summary_path.read_text(encoding="utf-8")

    reqs = state.get("requirements", {})
    recommended = (
        reqs.get("recommended_services", [])
        if isinstance(reqs.get("recommended_services"), list)
        else []
    )
    version = state.get("brief_version", 1)
    now = datetime.now(timezone.utc)

    existing_id = state.get("brief_id")
    if existing_id:
        brief = await Brief.get(existing_id)
        if brief:
            brief.markdown = markdown
            brief.ref_id = ref_id
            brief.recommended_services = recommended
            brief.file_path = str(summary_path) if summary_path.exists() else brief.file_path
            brief.version = version
            brief.updated_at = now
            await brief.save()
            return str(brief.id)

    tenant_id = state.get("tenant_id", "default")
    brief = Brief(
        tenant_id=tenant_id,
        user_id=state["user_id"],
        session_id=state.get("session_id", ""),
        ref_id=ref_id,
        client_name=client_name,
        markdown=markdown,
        recommended_services=recommended,
        file_path=str(summary_path) if summary_path.exists() else None,
        version=version,
    )
    await brief.insert()

    user = await User.get(state["user_id"])
    if user and user.email:
        summary_preview = markdown[:500] if markdown else ""
        await send_templated_email(
            tenant_id=tenant_id,
            template_key="brief_ready",
            to_email=user.email,
            variables={
                "client_name": client_name,
                "brief_link": f"/api/briefs/{brief.id}/download",
                "brief_summary": summary_preview,
            },
        )

    return str(brief.id)
