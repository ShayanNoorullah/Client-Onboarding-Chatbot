from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.schemas import AdminUserCreate, AdminUserUpdate, SessionUpdateRequest
from app.auth.dependencies import require_admin
from app.auth.passwords import hash_password
from app.llm.factory import check_ollama_health
from app.models.brief import Brief
from app.models.onboarding_session import OnboardingSessionDoc
from app.models.user import User
from app.storage.file_manager import delete_client_data
from app.storage.mongo_session_store import mongo_session_store

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/dashboard")
async def dashboard(_: User = Depends(require_admin)):
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    day_ago = now - timedelta(hours=24)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_users = await User.count()
    active_users = await User.find(User.last_login >= week_ago).count()
    new_users_7d = await User.find(User.created_at >= week_ago).count()
    total_sessions = await OnboardingSessionDoc.count()
    completed_briefs = await Brief.count()
    new_sessions_7d = await OnboardingSessionDoc.find(
        OnboardingSessionDoc.created_at >= week_ago
    ).count()
    sessions_today = await OnboardingSessionDoc.find(
        OnboardingSessionDoc.created_at >= today_start
    ).count()
    briefs_7d = await Brief.find(Brief.created_at >= week_ago).count()
    done_sessions = await OnboardingSessionDoc.find(OnboardingSessionDoc.done == True).count()
    consent_sessions = await OnboardingSessionDoc.find(
        OnboardingSessionDoc.consent_given == True
    ).count()
    active_sessions_24h = await OnboardingSessionDoc.find(
        OnboardingSessionDoc.updated_at >= day_ago
    ).count()
    admin_count = await User.find(User.role == "admin", User.is_active == True).count()
    user_count = await User.find(User.role == "user", User.is_active == True).count()

    completion_rate = round((done_sessions / total_sessions * 100) if total_sessions else 0, 1)
    consent_rate = round((consent_sessions / total_sessions * 100) if total_sessions else 0, 1)

    activity_by_day = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        sess_count = await OnboardingSessionDoc.find(
            OnboardingSessionDoc.created_at >= day_start,
            OnboardingSessionDoc.created_at < day_end,
        ).count()
        brief_count = await Brief.find(
            Brief.created_at >= day_start,
            Brief.created_at < day_end,
        ).count()
        activity_by_day.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "sessions": sess_count,
            "briefs": brief_count,
        })

    sessions_by_stage: dict[str, int] = {}
    for stage in ["greeting", "consent", "identity", "requirements", "clarify", "summarise"]:
        sessions_by_stage[stage] = await OnboardingSessionDoc.find(
            OnboardingSessionDoc.stage == stage
        ).count()
    project_types: dict[str, int] = {}
    sessions = await OnboardingSessionDoc.find(
        OnboardingSessionDoc.project_type != None
    ).to_list()
    for s in sessions:
        pt = s.project_type or "unknown"
        project_types[pt] = project_types.get(pt, 0) + 1
    recent = await OnboardingSessionDoc.find().sort(-OnboardingSessionDoc.updated_at).limit(20).to_list()
    return {
        "total_users": total_users,
        "active_users_7d": active_users,
        "new_users_7d": new_users_7d,
        "total_sessions": total_sessions,
        "new_sessions_7d": new_sessions_7d,
        "sessions_today": sessions_today,
        "completed_briefs": completed_briefs,
        "briefs_7d": briefs_7d,
        "completion_rate": completion_rate,
        "consent_rate": consent_rate,
        "active_sessions_24h": active_sessions_24h,
        "users_by_role": {"user": user_count, "admin": admin_count},
        "activity_by_day": activity_by_day,
        "sessions_by_stage": sessions_by_stage,
        "project_types": project_types,
        "recent_sessions": [s.to_summary() for s in recent],
        "ollama": check_ollama_health(),
    }


@router.get("/users")
async def list_users(
    _: User = Depends(require_admin),
    q: str | None = Query(default=None, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    users = await User.find().to_list()
    if q:
        needle = q.strip().lower()
        users = [
            u for u in users
            if needle in u.email.lower() or needle in u.full_name.lower()
        ]
    total = len(users)
    page = users[skip : skip + limit]
    return {"users": [u.to_public() for u in page], "total": total}


@router.post("/users")
async def create_user(body: AdminUserCreate, _: User = Depends(require_admin)):
    if await User.find_one(User.email == body.email.lower()):
        raise HTTPException(status_code=400, detail="Email exists")
    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role=body.role if body.role in ("user", "admin") else "user",
    )
    await user.insert()
    return {"user": user.to_public()}


@router.get("/users/{user_id}")
async def get_user(user_id: str, _: User = Depends(require_admin)):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user.to_public()}


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    body: AdminUserUpdate,
    current_admin: User = Depends(require_admin),
):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.role is not None and body.role in ("user", "admin"):
        if str(user.id) == str(current_admin.id) and body.role != user.role:
            raise HTTPException(status_code=400, detail="Cannot change your own role")
        if user.role == "admin" and body.role == "user":
            admin_count = await User.find(User.role == "admin", User.is_active == True).count()
            if admin_count <= 1:
                raise HTTPException(status_code=400, detail="Cannot remove the last admin")
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.password:
        user.password_hash = hash_password(body.password)
    await user.save()
    return {"user": user.to_public()}


@router.delete("/users/{user_id}")
async def deactivate_user(user_id: str, _: User = Depends(require_admin)):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await user.save()
    return {"status": "deactivated", "id": user_id}


@router.get("/sessions")
async def list_sessions(
    _: User = Depends(require_admin),
    user_id: str | None = None,
    stage: str | None = None,
    q: str | None = Query(default=None, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    if user_id and stage:
        docs = await OnboardingSessionDoc.find(
            OnboardingSessionDoc.user_id == user_id,
            OnboardingSessionDoc.stage == stage,
        ).to_list()
    elif user_id:
        docs = await OnboardingSessionDoc.find(
            OnboardingSessionDoc.user_id == user_id
        ).to_list()
    elif stage:
        docs = await OnboardingSessionDoc.find(
            OnboardingSessionDoc.stage == stage
        ).to_list()
    else:
        docs = await OnboardingSessionDoc.find().to_list()

    if q:
        from app.storage.session_display import session_matches_query, sort_sessions

        docs = [d for d in docs if session_matches_query(d, q)]
        docs = sort_sessions(docs)
    else:
        from app.storage.session_display import sort_sessions

        docs = sort_sessions(docs)

    total = len(docs)
    page = docs[skip : skip + limit]
    return {"sessions": [s.to_summary() for s in page], "total": total}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, _: User = Depends(require_admin)):
    doc = await OnboardingSessionDoc.find_one(OnboardingSessionDoc.session_id == session_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session": doc.to_summary(), "state": doc.state}


@router.patch("/sessions/{session_id}")
async def update_session(
    session_id: str,
    body: SessionUpdateRequest,
    _: User = Depends(require_admin),
):
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
async def delete_session(session_id: str, _: User = Depends(require_admin)):
    doc = await OnboardingSessionDoc.find_one(OnboardingSessionDoc.session_id == session_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found")
    client_name = doc.state.get("client_name")
    workspace_slug = doc.state.get("workspace_slug")
    await mongo_session_store.delete(session_id)
    if client_name:
        delete_client_data(client_name, workspace_slug)
    return {"status": "deleted", "session_id": session_id}


@router.get("/briefs")
async def list_all_briefs(
    _: User = Depends(require_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    total = await Brief.count()
    briefs = await Brief.find().sort(-Brief.created_at).skip(skip).limit(limit).to_list()
    return {"briefs": [b.to_public() for b in briefs], "total": total}


@router.delete("/briefs/{brief_id}")
async def admin_delete_brief(brief_id: str, _: User = Depends(require_admin)):
    brief = await Brief.get(brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    await brief.delete()
    return {"status": "deleted", "id": brief_id}
