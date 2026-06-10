from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.schemas import AdminUserCreate, AdminUserUpdate
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
    total_users = await User.count()
    active_users = await User.find(User.last_login >= week_ago).count()
    total_sessions = await OnboardingSessionDoc.count()
    completed_briefs = await Brief.count()
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
        "total_sessions": total_sessions,
        "completed_briefs": completed_briefs,
        "sessions_by_stage": sessions_by_stage,
        "project_types": project_types,
        "recent_sessions": [s.to_summary() for s in recent],
        "ollama": check_ollama_health(),
    }


@router.get("/users")
async def list_users(
    _: User = Depends(require_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    users = await User.find().skip(skip).limit(limit).to_list()
    total = await User.count()
    return {"users": [u.to_public() for u in users], "total": total}


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
async def update_user(user_id: str, body: AdminUserUpdate, _: User = Depends(require_admin)):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.role is not None and body.role in ("user", "admin"):
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
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    if user_id and stage:
        query = OnboardingSessionDoc.find(
            OnboardingSessionDoc.user_id == user_id,
            OnboardingSessionDoc.stage == stage,
        )
    elif user_id:
        query = OnboardingSessionDoc.find(OnboardingSessionDoc.user_id == user_id)
    elif stage:
        query = OnboardingSessionDoc.find(OnboardingSessionDoc.stage == stage)
    else:
        query = OnboardingSessionDoc.find()
    total = await query.count()
    sessions = await query.sort(-OnboardingSessionDoc.updated_at).skip(skip).limit(limit).to_list()
    return {"sessions": [s.to_summary() for s in sessions], "total": total}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, _: User = Depends(require_admin)):
    doc = await OnboardingSessionDoc.find_one(OnboardingSessionDoc.session_id == session_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session": doc.to_summary(), "state": doc.state}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, _: User = Depends(require_admin)):
    doc = await OnboardingSessionDoc.find_one(OnboardingSessionDoc.session_id == session_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found")
    client_name = doc.state.get("client_name")
    await mongo_session_store.delete(session_id)
    if client_name:
        delete_client_data(client_name)
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
