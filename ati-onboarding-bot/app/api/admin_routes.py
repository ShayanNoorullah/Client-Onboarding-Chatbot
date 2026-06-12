import csv
import io
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.api.schemas import AdminUserCreate, AdminUserUpdate, SessionUpdateRequest
from app.auth.dependencies import require_admin, require_permission
from app.auth.tenant_context import get_user_tenant_id
from app.auth.passwords import hash_password
from app.llm.factory import check_ollama_health
from app.models.app_module import ApplicationModule
from app.models.brief import Brief
from app.models.onboarding_session import OnboardingSessionDoc
from app.models.role import Role
from app.models.smtp_config import SmtpConfig
from app.models.user import User
from app.storage.file_manager import delete_client_data
from app.services.agent_metrics import metrics
from app.storage.mongo_session_store import mongo_session_store

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _tenant_id(user: User, request: Request) -> str:
    return get_user_tenant_id(user, request)


def _avg_turns_to_brief() -> float:
    if not metrics.sessions_completed:
        return 0.0
    return round(metrics.total_turns / metrics.sessions_completed, 1)


async def _enrich_session_summaries(sessions: list) -> list[dict]:
    user_ids = list({s.user_id for s in sessions if s.user_id})
    users_by_id: dict[str, User] = {}
    for uid in user_ids:
        try:
            user = await User.get(uid)
            if user:
                users_by_id[uid] = user
        except Exception:
            continue
    enriched = []
    for session in sessions:
        summary = session.to_summary()
        user = users_by_id.get(session.user_id or "")
        if user:
            summary["user_name"] = user.full_name
            summary["user_email"] = user.email
            summary["user_display"] = f"{user.full_name} ({user.email})"
        else:
            short_id = (session.user_id or "")[:8]
            summary["user_name"] = None
            summary["user_email"] = None
            summary["user_display"] = f"{short_id}…" if short_id else "—"
        enriched.append(summary)
    return enriched


@router.get("/pipeline/project-types")
async def pipeline_project_types(
    request: Request,
    admin: User = Depends(require_admin),
):
    tenant_id = _tenant_id(admin, request)
    pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {
            "$group": {
                "_id": {"$ifNull": ["$project_type", "unknown"]},
                "total": {"$sum": 1},
                "completed": {"$sum": {"$cond": ["$done", 1, 0]}},
                "in_progress": {
                    "$sum": {
                        "$cond": [
                            {"$and": [{"$not": "$done"}, {"$ne": ["$stage", "greeting"]}]},
                            1,
                            0,
                        ]
                    }
                },
                "last_activity": {"$max": "$updated_at"},
            }
        },
        {"$sort": {"total": -1}},
    ]
    rows = await OnboardingSessionDoc.aggregate(pipeline).to_list()
    summary_pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {
            "$group": {
                "_id": None,
                "total": {"$sum": 1},
                "completed": {"$sum": {"$cond": ["$done", 1, 0]}},
                "in_progress": {
                    "$sum": {
                        "$cond": [
                            {"$and": [{"$not": "$done"}, {"$ne": ["$stage", "greeting"]}]},
                            1,
                            0,
                        ]
                    }
                },
            }
        },
    ]
    summary_rows = await OnboardingSessionDoc.aggregate(summary_pipeline).to_list()
    summary = summary_rows[0] if summary_rows else {"total": 0, "completed": 0, "in_progress": 0}
    abandoned = max(0, summary.get("total", 0) - summary.get("completed", 0) - summary.get("in_progress", 0))
    return {
        "summary": {
            "total": summary.get("total", 0),
            "completed": summary.get("completed", 0),
            "in_progress": summary.get("in_progress", 0),
            "abandoned": abandoned,
        },
        "project_types": [
            {
                "project_type": row["_id"],
                "total": row["total"],
                "completed": row["completed"],
                "in_progress": row["in_progress"],
                "last_activity": row["last_activity"].isoformat() if row.get("last_activity") else None,
            }
            for row in rows
        ],
    }


@router.get("/dashboard")
async def dashboard(request: Request, admin: User = Depends(require_admin)):
    tenant_id = _tenant_id(admin, request)
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    day_ago = now - timedelta(hours=24)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_users = await User.find(User.tenant_id == tenant_id).count()
    total_users_active = await User.find(
        User.tenant_id == tenant_id, User.is_active == True
    ).count()
    active_users = await User.find(User.tenant_id == tenant_id, User.last_login >= week_ago).count()
    new_users_7d = await User.find(User.tenant_id == tenant_id, User.created_at >= week_ago).count()
    total_sessions = await OnboardingSessionDoc.find(OnboardingSessionDoc.tenant_id == tenant_id).count()
    completed_briefs = await Brief.find(Brief.tenant_id == tenant_id).count()
    new_sessions_7d = await OnboardingSessionDoc.find(
        OnboardingSessionDoc.tenant_id == tenant_id,
        OnboardingSessionDoc.created_at >= week_ago,
    ).count()
    sessions_today = await OnboardingSessionDoc.find(
        OnboardingSessionDoc.tenant_id == tenant_id,
        OnboardingSessionDoc.created_at >= today_start,
    ).count()
    briefs_7d = await Brief.find(Brief.tenant_id == tenant_id, Brief.created_at >= week_ago).count()
    done_sessions = await OnboardingSessionDoc.find(
        OnboardingSessionDoc.tenant_id == tenant_id,
        OnboardingSessionDoc.done == True,
    ).count()
    consent_sessions = await OnboardingSessionDoc.find(
        OnboardingSessionDoc.tenant_id == tenant_id,
        OnboardingSessionDoc.consent_given == True,
    ).count()
    active_sessions_24h = await OnboardingSessionDoc.find(
        OnboardingSessionDoc.tenant_id == tenant_id,
        OnboardingSessionDoc.updated_at >= day_ago,
    ).count()
    admin_count = await User.find(
        User.tenant_id == tenant_id, User.role == "admin", User.is_active == True
    ).count()
    user_count = await User.find(
        User.tenant_id == tenant_id, User.role == "user", User.is_active == True
    ).count()

    completion_rate = round((done_sessions / total_sessions * 100) if total_sessions else 0, 1)
    consent_rate = round((consent_sessions / total_sessions * 100) if total_sessions else 0, 1)

    activity_by_day = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        sess_count = await OnboardingSessionDoc.find(
            OnboardingSessionDoc.tenant_id == tenant_id,
            OnboardingSessionDoc.created_at >= day_start,
            OnboardingSessionDoc.created_at < day_end,
        ).count()
        brief_count = await Brief.find(
            Brief.tenant_id == tenant_id,
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
            OnboardingSessionDoc.tenant_id == tenant_id,
            OnboardingSessionDoc.stage == stage,
            OnboardingSessionDoc.done == False,
        ).count()
    sessions_by_stage["completed"] = done_sessions
    project_types: dict[str, int] = {}
    sessions = await OnboardingSessionDoc.find(
        OnboardingSessionDoc.tenant_id == tenant_id,
        OnboardingSessionDoc.project_type != None,
    ).to_list()
    for s in sessions:
        pt = s.project_type or "unknown"
        project_types[pt] = project_types.get(pt, 0) + 1
    recent = await OnboardingSessionDoc.find(
        OnboardingSessionDoc.tenant_id == tenant_id
    ).sort(-OnboardingSessionDoc.updated_at).limit(20).to_list()
    total_roles = await Role.find(Role.is_active == True).count()
    total_modules = await ApplicationModule.find(ApplicationModule.is_active == True).count()
    smtp_configured = await SmtpConfig.find_one(SmtpConfig.tenant_id == tenant_id) is not None
    return {
        "total_users": total_users,
        "total_users_active": total_users_active,
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
        "recent_sessions": await _enrich_session_summaries(recent),
        "ollama": check_ollama_health(tenant_id),
        "agent_metrics": metrics.summary(),
        "avg_turns_to_brief": _avg_turns_to_brief(),
        "drop_off_by_stage": sessions_by_stage,
        "total_roles": total_roles,
        "total_modules": total_modules,
        "smtp_configured": smtp_configured,
    }


@router.get("/reports/export")
async def export_reports(
    request: Request,
    admin: User = Depends(require_permission("Reports", "Reports", "view")),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
):
    tenant_id = _tenant_id(admin, request)
    sessions = await OnboardingSessionDoc.find(
        OnboardingSessionDoc.tenant_id == tenant_id
    ).sort(-OnboardingSessionDoc.created_at).to_list()
    if from_date:
        try:
            start = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            sessions = [s for s in sessions if s.created_at >= start]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid from_date")
    if to_date:
        try:
            end = datetime.fromisoformat(to_date.replace("Z", "+00:00"))
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            sessions = [s for s in sessions if s.created_at <= end]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid to_date")

    all_users = await User.find_all().to_list()
    email_by_id = {str(u.id): u.email for u in all_users}

    session_ids = [s.session_id for s in sessions]
    brief_session_ids = set()
    if session_ids:
        all_briefs = await Brief.find_all().to_list()
        brief_session_ids = {b.session_id for b in all_briefs if b.session_id in session_ids}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "session_id", "user_email", "stage", "project_type",
        "created_at", "completed", "brief_generated",
    ])
    for s in sessions:
        writer.writerow([
            s.session_id,
            email_by_id.get(s.user_id, ""),
            s.stage,
            s.project_type or "",
            s.created_at.isoformat(),
            s.done,
            s.session_id in brief_session_ids,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sessions_export.csv"},
    )


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
    return {"sessions": await _enrich_session_summaries(page), "total": total}


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
