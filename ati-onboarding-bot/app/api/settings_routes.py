import math
from datetime import datetime, timezone

from beanie.operators import Set
from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.seeders import ensure_page_actions
from app.api.schemas import (
    ActionCreate,
    ActionPatch,
    ActionUpdate,
    ModuleCreate,
    ModuleUpdate,
    PageCreate,
    PageUpdate,
    RoleCreate,
    RoleUpdate,
    UserCreateAdmin,
    UserPatchAdmin,
    UserUpdateAdmin,
)
from app.auth.dependencies import require_admin, require_permission
from app.auth.passwords import hash_password
from app.models.app_action import ApplicationAction
from app.models.app_module import ApplicationModule
from app.models.app_page import ApplicationPage
from app.models.role import Role
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["admin-settings"])

ADMIN_ROLE_NAMES = {"Admin", "Super Admin"}
MASKED_PASSWORD = "••••••••"


def _paginate(items: list, page: int, limit: int) -> dict:
    total = len(items)
    pages = max(1, math.ceil(total / limit)) if limit else 1
    start = (page - 1) * limit
    return {
        "total": total,
        "page": page,
        "pages": pages,
        "items": items[start : start + limit],
    }


def _role_to_admin(user: User) -> str:
    return "admin" if user.role_name in ADMIN_ROLE_NAMES else "user"


def _sync_role_field(role_name: str) -> str:
    return "admin" if role_name in ADMIN_ROLE_NAMES else "user"


# ── ROLES ──────────────────────────────────────────────────────────────────


@router.get("/roles")
async def list_roles(
    _: User = Depends(require_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=200),
    search: str | None = Query(default=None, max_length=100),
):
    roles = await Role.find().sort(+Role.sort_order, +Role.name).to_list()
    if search:
        needle = search.strip().lower()
        roles = [r for r in roles if needle in r.name.lower() or needle in r.description.lower()]
    result = _paginate(roles, page, limit)
    return {
        "roles": [r.to_dict() for r in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "pages": result["pages"],
    }


@router.post("/roles")
async def create_role(body: RoleCreate, admin: User = Depends(require_admin)):
    if await Role.find_one(Role.name == body.name):
        raise HTTPException(status_code=400, detail="Role name already exists")
    now = datetime.now(timezone.utc)
    role = Role(
        name=body.name,
        description=body.description,
        is_active=body.is_active,
        permissions=body.permissions,
        created_by=admin.email,
        created_at=now,
        updated_at=now,
    )
    await role.insert()
    return {"role": role.to_dict()}


@router.get("/roles/{role_id}")
async def get_role(role_id: str, _: User = Depends(require_admin)):
    role = await Role.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return {"role": role.to_dict()}


@router.put("/roles/{role_id}")
async def update_role(role_id: str, body: RoleUpdate, _: User = Depends(require_admin)):
    role = await Role.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    old_name = role.name
    if body.name and body.name != role.name:
        if await Role.find_one(Role.name == body.name):
            raise HTTPException(status_code=400, detail="Role name already exists")
        role.name = body.name
        await User.find(User.role_name == old_name).update(Set({User.role_name: body.name}))
    if body.description is not None:
        role.description = body.description
    if body.is_active is not None:
        role.is_active = body.is_active
    if body.permissions is not None:
        role.permissions = body.permissions
    role.updated_at = datetime.now(timezone.utc)
    await role.save()
    return {"role": role.to_dict()}


@router.delete("/roles/{role_id}")
async def delete_role(role_id: str, _: User = Depends(require_admin)):
    role = await Role.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    user_count = await User.find(User.role_name == role.name).count()
    if user_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete role: {user_count} user(s) assigned",
        )
    await role.delete()
    return {"status": "deleted", "id": role_id}


# ── USERS ──────────────────────────────────────────────────────────────────


@router.get("/users")
async def list_settings_users(
    _: User = Depends(require_permission("Settings", "User", "view")),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=200),
    search: str | None = Query(default=None, max_length=100),
    role_name: str | None = Query(default=None, max_length=100),
):
    users = await User.find().sort(-User.created_at).to_list()
    if role_name:
        users = [u for u in users if u.role_name == role_name]
    if search:
        needle = search.strip().lower()
        users = [
            u for u in users
            if needle in u.email.lower()
            or needle in u.full_name.lower()
            or (u.username and needle in u.username.lower())
        ]
    result = _paginate(users, page, limit)
    return {
        "users": [u.to_public() for u in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "pages": result["pages"],
    }


@router.post("/users")
async def create_settings_user(
    body: UserCreateAdmin,
    admin: User = Depends(require_permission("Settings", "User", "insert")),
):
    email = body.email.lower()
    if await User.find_one(User.email == email):
        raise HTTPException(status_code=400, detail="Email already exists")
    if body.username and await User.find_one(User.username == body.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(
        email=email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        username=body.username,
        role_name=body.role_name,
        role=_sync_role_field(body.role_name),
        is_active=body.is_active,
        tenant_id=admin.tenant_id or "default",
    )
    await user.insert()
    return {"user": user.to_public()}


@router.get("/users/{user_id}")
async def get_settings_user(
    user_id: str,
    _: User = Depends(require_permission("Settings", "User", "view")),
):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user.to_public()}


@router.put("/users/{user_id}")
async def update_settings_user(
    user_id: str,
    body: UserUpdateAdmin,
    current_admin: User = Depends(require_permission("Settings", "User", "update")),
):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.username is not None:
        if body.username:
            existing = await User.find_one(User.username == body.username)
            if existing and str(existing.id) != str(user.id):
                raise HTTPException(status_code=400, detail="Username already exists")
        user.username = body.username or None
    if body.role_name is not None:
        if str(user.id) == str(current_admin.id) and body.role_name not in ADMIN_ROLE_NAMES:
            raise HTTPException(status_code=400, detail="Cannot demote yourself")
        if user.role == "admin" and body.role_name not in ADMIN_ROLE_NAMES:
            admin_count = await User.find(User.role == "admin", User.is_active == True).count()
            if admin_count <= 1:
                raise HTTPException(status_code=400, detail="Cannot remove the last admin")
        user.role_name = body.role_name
        user.role = _sync_role_field(body.role_name)
    if body.is_active is not None:
        user.is_active = body.is_active
    await user.save()
    return {"user": user.to_public()}


@router.patch("/users/{user_id}")
async def patch_settings_user(
    user_id: str,
    body: UserPatchAdmin,
    current_admin: User = Depends(require_permission("Settings", "User", "update")),
):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not body.is_active and user.role == "admin":
        admin_count = await User.find(User.role == "admin", User.is_active == True).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot deactivate the last admin")
    user.is_active = body.is_active
    await user.save()
    return {"user": user.to_public()}


@router.delete("/users/{user_id}")
async def delete_settings_user(
    user_id: str,
    current_admin: User = Depends(require_permission("Settings", "User", "delete")),
    hard: bool = Query(default=False),
):
    if str(user_id) == str(current_admin.id):
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if hard:
        await user.delete()
        return {"status": "deleted", "id": user_id}
    user.is_active = False
    await user.save()
    return {"status": "deactivated", "id": user_id}


# ── MODULES ────────────────────────────────────────────────────────────────


@router.get("/modules")
async def list_modules(_: User = Depends(require_admin)):
    modules = await ApplicationModule.find().sort(ApplicationModule.sort_order).to_list()
    return {"modules": [m.to_dict() for m in modules]}


@router.post("/modules")
async def create_module(body: ModuleCreate, admin: User = Depends(require_admin)):
    if await ApplicationModule.find_one(ApplicationModule.name == body.name):
        raise HTTPException(status_code=400, detail="Module name already exists")
    now = datetime.now(timezone.utc)
    mod = ApplicationModule(
        name=body.name,
        icon=body.icon,
        sort_order=body.sort_order,
        is_active=body.is_active,
        created_by=admin.email,
        created_at=now,
        updated_at=now,
    )
    await mod.insert()
    return {"module": mod.to_dict()}


@router.put("/modules/{module_id}")
async def update_module(module_id: str, body: ModuleUpdate, _: User = Depends(require_admin)):
    mod = await ApplicationModule.get(module_id)
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")
    if body.name and body.name != mod.name:
        if await ApplicationModule.find_one(ApplicationModule.name == body.name):
            raise HTTPException(status_code=400, detail="Module name already exists")
        old_name = mod.name
        mod.name = body.name
        await ApplicationPage.find(ApplicationPage.module_name == old_name).update(
            Set({ApplicationPage.module_name: body.name})
        )
    if body.icon is not None:
        mod.icon = body.icon
    if body.sort_order is not None:
        mod.sort_order = body.sort_order
    if body.is_active is not None:
        mod.is_active = body.is_active
    mod.updated_at = datetime.now(timezone.utc)
    await mod.save()
    return {"module": mod.to_dict()}


@router.delete("/modules/{module_id}")
async def delete_module(module_id: str, _: User = Depends(require_admin)):
    mod = await ApplicationModule.get(module_id)
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")
    page_count = await ApplicationPage.find(ApplicationPage.module_name == mod.name).count()
    if page_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete module: {page_count} page(s) associated",
        )
    await mod.delete()
    return {"status": "deleted", "id": module_id}


# ── PAGES ──────────────────────────────────────────────────────────────────


@router.get("/pages")
async def list_pages(
    _: User = Depends(require_admin),
    module_name: str | None = Query(default=None, max_length=100),
):
    query = ApplicationPage.find()
    if module_name:
        query = ApplicationPage.find(ApplicationPage.module_name == module_name)
    pages = await query.sort(ApplicationPage.sort_order).to_list()
    return {"pages": [p.to_dict() for p in pages]}


@router.post("/pages")
async def create_page(body: PageCreate, admin: User = Depends(require_admin)):
    if not await ApplicationModule.find_one(ApplicationModule.name == body.module_name):
        raise HTTPException(status_code=400, detail="Module not found")
    now = datetime.now(timezone.utc)
    page = ApplicationPage(
        module_name=body.module_name,
        page_name=body.page_name,
        route=body.route,
        sort_order=body.sort_order,
        is_active=body.is_active,
        created_by=admin.email,
        created_at=now,
        updated_at=now,
    )
    await page.insert()
    await ensure_page_actions(page.page_name)
    return {"page": page.to_dict()}


@router.put("/pages/{page_id}")
async def update_page(page_id: str, body: PageUpdate, _: User = Depends(require_admin)):
    page = await ApplicationPage.get(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    if body.module_name is not None:
        if not await ApplicationModule.find_one(ApplicationModule.name == body.module_name):
            raise HTTPException(status_code=400, detail="Module not found")
        page.module_name = body.module_name
    if body.page_name is not None:
        page.page_name = body.page_name
    if body.route is not None:
        page.route = body.route
    if body.sort_order is not None:
        page.sort_order = body.sort_order
    if body.is_active is not None:
        page.is_active = body.is_active
    page.updated_at = datetime.now(timezone.utc)
    await page.save()
    return {"page": page.to_dict()}


@router.delete("/pages/{page_id}")
async def delete_page(page_id: str, _: User = Depends(require_admin)):
    page = await ApplicationPage.get(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    await page.delete()
    return {"status": "deleted", "id": page_id}


# ── ACTIONS ────────────────────────────────────────────────────────────────


async def _action_key_in_use(page_name: str, action_key: str, exclude_id: str | None = None) -> bool:
    existing = await ApplicationAction.find_one(
        ApplicationAction.page_name == page_name,
        ApplicationAction.action_key == action_key,
    )
    if not existing:
        return False
    return str(existing.id) != exclude_id


async def _action_referenced_in_roles(page_name: str, action_key: str) -> bool:
    pages = await ApplicationPage.find(ApplicationPage.page_name == page_name).to_list()
    if not pages:
        return False
    module_name = pages[0].module_name
    for role in await Role.find_all().to_list():
        perms = role.permissions or {}
        if perms.get(module_name, {}).get(page_name, {}).get(action_key):
            return True
    return False


def _sort_actions(actions: list[ApplicationAction]) -> list[ApplicationAction]:
    return sorted(
        actions,
        key=lambda a: (-int(a.is_pinned), a.sort_order, a.page_name, a.action_key),
    )


@router.get("/actions")
async def list_actions(
    _: User = Depends(require_admin),
    page_name: str | None = Query(default=None, max_length=100),
    search: str | None = Query(default=None, max_length=100),
    pinned_only: bool = Query(default=False),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=200),
):
    actions = await ApplicationAction.find().to_list()
    if page_name:
        actions = [a for a in actions if a.page_name == page_name]
    if pinned_only:
        actions = [a for a in actions if a.is_pinned]
    if search:
        needle = search.strip().lower()
        actions = [
            a for a in actions
            if needle in a.page_name.lower()
            or needle in a.action_name.lower()
            or needle in a.action_key.lower()
        ]
    actions = _sort_actions(actions)
    result = _paginate(actions, page, limit)
    return {
        "actions": [a.to_dict() for a in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "pages": result["pages"],
    }


@router.get("/actions/{action_id}")
async def get_action(action_id: str, _: User = Depends(require_admin)):
    action = await ApplicationAction.get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return {"action": action.to_dict()}


@router.post("/actions")
async def create_action(body: ActionCreate, admin: User = Depends(require_admin)):
    if not await ApplicationPage.find_one(ApplicationPage.page_name == body.page_name):
        raise HTTPException(status_code=400, detail="Page not found")
    action_key = body.action_key.strip().lower()
    if await _action_key_in_use(body.page_name, action_key):
        raise HTTPException(status_code=400, detail="Action key already exists for this page")
    now = datetime.now(timezone.utc)
    action = ApplicationAction(
        page_name=body.page_name,
        action_name=body.action_name,
        action_key=action_key,
        sort_order=body.sort_order,
        is_pinned=body.is_pinned,
        is_active=body.is_active,
        created_by=admin.email,
        created_at=now,
        updated_at=now,
    )
    await action.insert()
    return {"action": action.to_dict()}


@router.put("/actions/{action_id}")
async def update_action(action_id: str, body: ActionUpdate, _: User = Depends(require_admin)):
    action = await ApplicationAction.get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    page_name = body.page_name or action.page_name
    if body.page_name is not None:
        if not await ApplicationPage.find_one(ApplicationPage.page_name == body.page_name):
            raise HTTPException(status_code=400, detail="Page not found")
        action.page_name = body.page_name
    if body.action_name is not None:
        action.action_name = body.action_name
    if body.action_key is not None:
        action_key = body.action_key.strip().lower()
        if await _action_key_in_use(page_name, action_key, exclude_id=action_id):
            raise HTTPException(status_code=400, detail="Action key already exists for this page")
        action.action_key = action_key
    if body.sort_order is not None:
        action.sort_order = body.sort_order
    if body.is_pinned is not None:
        action.is_pinned = body.is_pinned
    if body.is_active is not None:
        action.is_active = body.is_active
    action.updated_at = datetime.now(timezone.utc)
    await action.save()
    return {"action": action.to_dict()}


@router.patch("/actions/{action_id}")
async def patch_action(action_id: str, body: ActionPatch, _: User = Depends(require_admin)):
    action = await ApplicationAction.get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    if body.is_active is not None:
        action.is_active = body.is_active
    if body.is_pinned is not None:
        action.is_pinned = body.is_pinned
    action.updated_at = datetime.now(timezone.utc)
    await action.save()
    return {"action": action.to_dict()}


@router.delete("/actions/{action_id}")
async def delete_action(action_id: str, _: User = Depends(require_admin)):
    action = await ApplicationAction.get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    if await _action_referenced_in_roles(action.page_name, action.action_key):
        raise HTTPException(
            status_code=400,
            detail="Action is referenced in role permissions; remove from roles first",
        )
    await action.delete()
    return {"status": "deleted", "id": action_id}
