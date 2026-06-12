from fastapi import APIRouter, HTTPException

from app.models.brief import Brief
from app.models.onboarding_session import OnboardingSessionDoc
from app.models.user import User
from app.services.email_service import send_templated_email
from app.services.magic_link_service import (
    MAGIC_LINK_PURPOSE,
    PORTAL_PURPOSE,
    create_magic_token,
    decode_token,
)
from app.services.system_config_service import get_effective_settings

router = APIRouter(tags=["portal"])


@router.get("/api/portal/brief/{token}")
async def get_portal_brief(token: str):
    payload = decode_token(token, PORTAL_PURPOSE)
    if not payload or not payload.get("brief_id"):
        raise HTTPException(status_code=401, detail="Invalid or expired portal link")
    brief = await Brief.get(payload["brief_id"])
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    return {
        "ref_id": brief.ref_id,
        "client_name": brief.client_name,
        "created_at": brief.created_at.isoformat(),
        "recommended_services": brief.recommended_services,
        "download_url": f"/api/briefs/{brief.id}/download",
        "status": "completed",
    }


@router.post("/api/auth/magic-link")
async def request_magic_link(body: dict):
    email = (body.get("email") or "").lower().strip()
    session_id = body.get("session_id", "")
    if not email or not session_id:
        raise HTTPException(status_code=400, detail="email and session_id required")
    user = await User.find_one(User.email == email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session = await OnboardingSessionDoc.find_one(OnboardingSessionDoc.session_id == session_id)
    if not session or session.user_id != str(user.id):
        raise HTTPException(status_code=404, detail="Session not found")
    token = create_magic_token(user_id=str(user.id), session_id=session_id)
    link = f"/chat.html?magic={token}"
    tenant_id = user.tenant_id or "default"
    await send_templated_email(
        tenant_id=tenant_id,
        template_key="session_magic_link",
        to_email=user.email,
        variables={"client_name": user.full_name, "session_link": link},
    )
    return {"message": "Magic link sent", "link": link}


@router.get("/api/auth/magic-link/verify")
async def verify_magic_link(token: str):
    payload = decode_token(token, MAGIC_LINK_PURPOSE)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired magic link")
    return {
        "user_id": payload.get("sub"),
        "session_id": payload.get("session_id"),
        "redirect": f"/chat.html?session={payload.get('session_id')}",
    }
