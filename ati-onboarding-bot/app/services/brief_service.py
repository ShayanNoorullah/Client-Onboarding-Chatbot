from datetime import datetime, timezone

from app.models.brief import Brief
from app.models.user import User
from app.services.email_service import send_templated_email
from app.services.magic_link_service import create_portal_token
from app.services.notification_service import EVENT_BRIEF_CREATED, dispatch_event
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
    brief_link = f"/api/briefs/{brief.id}/download"
    portal_token = create_portal_token(brief_id=str(brief.id), tenant_id=tenant_id)
    portal_link = f"/portal.html?token={portal_token}"
    summary_preview = markdown[:500] if markdown else ""
    project_type = state.get("collected_requirements", {}).get("project_type", "Not specified")
    if isinstance(state.get("requirements"), dict):
        project_type = state["requirements"].get("project_type", project_type)

    email_vars = {
        "client_name": client_name,
        "brief_link": brief_link,
        "brief_summary": summary_preview,
        "product_name": "Client Onboarding Agent",
        "portal_link": portal_link,
    }
    admin_vars = {
        "client_name": client_name,
        "user_email": user.email if user else "unknown",
        "brief_link": brief_link,
        "brief_summary": summary_preview,
        "project_type": str(project_type),
        "ref_id": ref_id,
    }

    if user and user.email:
        await send_templated_email(
            tenant_id=tenant_id,
            template_key="brief_ready",
            to_email=user.email,
            variables=email_vars,
        )

    await dispatch_event(
        tenant_id,
        EVENT_BRIEF_CREATED,
        {
            "brief_id": str(brief.id),
            "ref_id": ref_id,
            "client_name": client_name,
            "user_email": user.email if user else None,
            "project_type": str(project_type),
            "portal_link": portal_link,
        },
        email_template="brief_submitted_admin",
        email_variables=admin_vars,
        notify_admins=True,
        admin_title="New client brief submitted",
        admin_body=f"{client_name} submitted a new brief ({ref_id})",
        admin_link=f"/admin/briefs.html",
    )

    return str(brief.id)
