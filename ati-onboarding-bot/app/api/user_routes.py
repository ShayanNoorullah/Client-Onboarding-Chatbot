from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.schemas import ProfileUpdateRequest, SessionUpdateRequest, UserPreferencesUpdate
from app.services.user_preferences import apply_preference_updates, merge_preferences
from app.agent.routing import can_request_manual_brief
from app.auth.dependencies import get_current_user
from app.auth.passwords import hash_password
from app.models.brief import Brief
from app.models.user import User
from app.storage.mongo_session_store import mongo_session_store

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/profile")
async def get_profile(user: User = Depends(get_current_user)):
    return {"user": user.to_public()}


@router.get("/preferences")
async def get_preferences(user: User = Depends(get_current_user)):
    return {"preferences": merge_preferences(user.preferences)}


@router.put("/preferences")
async def update_preferences(body: UserPreferencesUpdate, user: User = Depends(get_current_user)):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No preferences to update")
    user.preferences = apply_preference_updates(user.preferences, updates)
    await user.save()
    return {"preferences": user.preferences}


@router.put("/profile")
async def update_profile(body: ProfileUpdateRequest, user: User = Depends(get_current_user)):
    if body.full_name:
        user.full_name = body.full_name
    if body.password:
        user.password_hash = hash_password(body.password)
    await user.save()
    return {"user": user.to_public()}


@router.post("/sessions")
async def create_session(user: User = Depends(get_current_user)):
    from app.storage.file_manager import sanitise_name

    name = sanitise_name(user.full_name)
    state = await mongo_session_store.create(str(user.id), user.full_name)
    return {"session_id": state["session_id"], "stage": state["stage"]}


@router.get("/sessions")
async def list_sessions(
    user: User = Depends(get_current_user),
    q: str | None = Query(default=None, max_length=100),
):
    sessions = await mongo_session_store.list_for_user(str(user.id), q=q)
    return {"sessions": sessions}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, user: User = Depends(get_current_user)):
    try:
        state = await mongo_session_store.get(session_id, str(user.id))
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not your session")

    brief_url = None
    if state.get("brief_id"):
        brief_url = f"/api/briefs/{state['brief_id']}/download"

    return {
        "session_id": session_id,
        "stage": state.get("stage"),
        "done": state.get("done", False),
        "messages": state.get("messages", []),
        "requirements_complete": state.get("requirements_complete", False),
        "readiness_score": state.get("readiness_score", 0.0),
        "missing_fields": state.get("missing_fields", []),
        "brief_download_url": brief_url,
        "consent_given": state.get("consent_given", False),
        "consent_required": not state.get("consent_given", False),
        "brief_version": state.get("brief_version", 1),
        "show_generate_brief": can_request_manual_brief(state),
    }


@router.patch("/sessions/{session_id}")
async def update_session(
    session_id: str,
    body: SessionUpdateRequest,
    user: User = Depends(get_current_user),
):
    try:
        await mongo_session_store.get(session_id, str(user.id))
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not your session")

    fields_set = body.model_fields_set
    if "title" not in fields_set and "pinned" not in fields_set:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        doc = await mongo_session_store.update_metadata(
            session_id,
            title=body.title,
            pinned=body.pinned,
            title_set="title" in fields_set,
            pinned_set="pinned" in fields_set,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"session": doc.to_summary()}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user: User = Depends(get_current_user)):
    try:
        await mongo_session_store.get(session_id, str(user.id))
        await mongo_session_store.delete(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not your session")
    return {"status": "deleted", "session_id": session_id}


@router.get("/briefs")
async def list_briefs(user: User = Depends(get_current_user)):
    briefs = await Brief.find(Brief.user_id == str(user.id)).sort(-Brief.created_at).to_list()
    return {"briefs": [b.to_public() for b in briefs]}
