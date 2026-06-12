import logging
from datetime import datetime, timezone

from app.agent.task_router import PROJECT_TYPE_ALIASES
from app.config import settings
from app.models.app_action import ApplicationAction
from app.models.app_module import ApplicationModule
from app.models.app_page import ApplicationPage
from app.models.brief import Brief
from app.models.email_template import EmailTemplate
from app.models.follow_up_rule import FollowUpRule
from app.models.onboarding_session import OnboardingSessionDoc
from app.models.role import PermissionsMap, Role
from app.models.smtp_config import SmtpConfig
from app.models.ai_config import AiConfig
from app.models.system_config import SystemConfig
from app.models.tenant import Tenant
from app.models.user import User
from app.services.ai_config_service import warm_ai_config_cache
from app.services.system_config_service import warm_config_cache

logger = logging.getLogger(__name__)

SYSTEM_CREATOR = "system@ati.local"

DEFAULT_MODULES = [
    {"name": "Dashboard", "icon": "fa fa-th-large", "sort_order": 1},
    {"name": "Pipeline", "icon": "fa fa-circle-nodes", "sort_order": 2},
    {"name": "Configuration", "icon": "fa fa-sliders", "sort_order": 3},
    {"name": "Settings", "icon": "fa fa-cog", "sort_order": 4},
    {"name": "Reports", "icon": "fa fa-chart-bar", "sort_order": 5},
]

PROJECT_TYPE_LABELS = {
    "website_development": "Website Development",
    "mobile_app_development": "Mobile App Development",
    "software_integration": "Software Integration",
    "consulting": "Consulting",
    "mortgage_website_development": "Mortgage Website Development",
}

ACTION_KEYS = [
    ("View", "view"),
    ("Insert", "insert"),
    ("Update", "update"),
    ("Delete", "delete"),
]

USER_VIEW_MODULES = {"Dashboard", "Pipeline", "Reports"}
USER_VIEW_PAGES = {
    "Dashboard",
    "Onboarding Sessions",
    "Briefs",
    "Project Types",
    "Reports",
}


def _canonical_project_types() -> list[str]:
    return sorted(set(PROJECT_TYPE_ALIASES.values()))


def _default_page_defs() -> list[dict]:
    pages: list[dict] = [
        {"module_name": "Dashboard", "page_name": "Dashboard", "route": "/admin/dashboard.html", "sort_order": 1},
        {"module_name": "Reports", "page_name": "Reports", "route": "/admin/reports.html", "sort_order": 1},
        {"module_name": "Pipeline", "page_name": "Onboarding Sessions", "route": "/admin/sessions.html", "sort_order": 1},
        {"module_name": "Pipeline", "page_name": "Briefs", "route": "/admin/briefs.html", "sort_order": 2},
        {"module_name": "Pipeline", "page_name": "Project Types", "route": "/admin/pipeline-types.html", "sort_order": 3},
        {"module_name": "Configuration", "page_name": "AI Configuration", "route": "/admin/config-ai.html", "sort_order": 1},
        {"module_name": "Configuration", "page_name": "System Configuration", "route": "/admin/config-system.html", "sort_order": 2},
        {"module_name": "Configuration", "page_name": "SMTP", "route": "/admin/config-smtp.html", "sort_order": 3},
        {"module_name": "Configuration", "page_name": "Email Templates", "route": "/admin/config-email-templates.html", "sort_order": 4},
        {"module_name": "Configuration", "page_name": "Follow-up Timing", "route": "/admin/config-followup.html", "sort_order": 5},
        {"module_name": "Configuration", "page_name": "Workspace", "route": "/admin/config-tenant.html", "sort_order": 6},
        {"module_name": "Configuration", "page_name": "API Keys", "route": "/admin/config-api-keys.html", "sort_order": 7},
        {"module_name": "Configuration", "page_name": "Usage & Limits", "route": "/admin/config-usage.html", "sort_order": 8},
        {"module_name": "Settings", "page_name": "Application Action", "route": "/admin/settings-actions.html", "sort_order": 1},
        {"module_name": "Settings", "page_name": "Application Module", "route": "/admin/settings-modules.html", "sort_order": 2},
        {"module_name": "Settings", "page_name": "Application Page", "route": "/admin/settings-pages.html", "sort_order": 3},
        {"module_name": "Settings", "page_name": "Role", "route": "/admin/settings-roles.html", "sort_order": 4},
        {"module_name": "Settings", "page_name": "User", "route": "/admin/settings-users.html", "sort_order": 5},
        {"module_name": "Settings", "page_name": "Audit Log", "route": "/admin/settings-audit.html", "sort_order": 6},
    ]
    order = 4
    for pt in _canonical_project_types():
        label = PROJECT_TYPE_LABELS.get(pt, pt.replace("_", " ").title())
        pages.append({
            "module_name": "Pipeline",
            "page_name": label,
            "route": f"/admin/pipeline-types.html?type={pt}",
            "sort_order": order,
        })
        order += 1
    return pages


def build_permissions_map(full_access: bool) -> PermissionsMap:
    perms: PermissionsMap = {}
    for page_def in _default_page_defs():
        module = page_def["module_name"]
        page = page_def["page_name"]
        perms.setdefault(module, {})
        if full_access:
            perms[module][page] = {"view": True, "insert": True, "update": True, "delete": True}
        else:
            can_view = module in USER_VIEW_MODULES and page in USER_VIEW_PAGES
            perms[module][page] = {
                "view": can_view,
                "insert": False,
                "update": False,
                "delete": False,
            }
    return perms


async def seed_modules() -> None:
    if await ApplicationModule.count() > 0:
        return
    now = datetime.now(timezone.utc)
    for mod in DEFAULT_MODULES:
        await ApplicationModule(
            name=mod["name"],
            icon=mod["icon"],
            sort_order=mod["sort_order"],
            is_active=True,
            created_by=SYSTEM_CREATOR,
            created_at=now,
            updated_at=now,
        ).insert()
    logger.info("Seeded %d application modules", len(DEFAULT_MODULES))


async def seed_pages() -> None:
    if await ApplicationPage.count() > 0:
        return
    now = datetime.now(timezone.utc)
    for page_def in _default_page_defs():
        await ApplicationPage(
            module_name=page_def["module_name"],
            page_name=page_def["page_name"],
            route=page_def["route"],
            sort_order=page_def["sort_order"],
            is_active=True,
            created_by=SYSTEM_CREATOR,
            created_at=now,
            updated_at=now,
        ).insert()
    logger.info("Seeded application pages")


async def seed_actions() -> None:
    if await ApplicationAction.count() > 0:
        return
    now = datetime.now(timezone.utc)
    pages = await ApplicationPage.find().to_list()
    count = 0
    for page in pages:
        for action_name, action_key in ACTION_KEYS:
            await ApplicationAction(
                page_name=page.page_name,
                action_name=action_name,
                action_key=action_key,
                is_active=True,
                created_by=SYSTEM_CREATOR,
                created_at=now,
                updated_at=now,
            ).insert()
            count += 1
    logger.info("Seeded %d application actions", count)


async def seed_roles() -> None:
    if await Role.count() > 0:
        return
    now = datetime.now(timezone.utc)
    role_defs = [
        ("Super Admin", "Super administrative access", True, 1),
        ("Admin", "Full administrative access", True, 2),
        ("User", "Limited user access", False, 3),
    ]
    for name, description, full_access, sort_order in role_defs:
        await Role(
            name=name,
            description=description,
            sort_order=sort_order,
            is_active=True,
            permissions=build_permissions_map(full_access),
            created_by=SYSTEM_CREATOR,
            created_at=now,
            updated_at=now,
        ).insert()
    logger.info("Seeded default roles")


DEFAULT_EMAIL_TEMPLATES = [
    {
        "key": "welcome",
        "name": "Welcome Email",
        "subject": "Welcome to {{product_name}}",
        "body_html": "<p>Hi {{client_name}}, welcome to {{product_name}}!</p>",
        "body_text": "Hi {{client_name}}, welcome to {{product_name}}!",
        "variables": ["client_name", "product_name"],
    },
    {
        "key": "brief_ready",
        "name": "Brief Ready",
        "subject": "Your project brief is ready",
        "body_html": "<p>Hi {{client_name}}, your brief is ready. <a href=\"{{brief_link}}\">View brief</a></p>",
        "body_text": "Hi {{client_name}}, your brief is ready: {{brief_link}}",
        "variables": ["client_name", "brief_link", "brief_summary"],
    },
    {
        "key": "session_reminder",
        "name": "Session Reminder",
        "subject": "Continue your onboarding session",
        "body_html": "<p>Hi {{client_name}}, you have an incomplete session. <a href=\"{{session_link}}\">Continue here</a></p>",
        "body_text": "Hi {{client_name}}, continue your session: {{session_link}}",
        "variables": ["client_name", "session_link", "stage"],
    },
    {
        "key": "session_abandoned",
        "name": "Session Abandoned",
        "subject": "We missed you — resume your project brief",
        "body_html": "<p>Hi {{client_name}}, your session at stage {{stage}} is waiting. <a href=\"{{session_link}}\">Resume</a></p>",
        "body_text": "Hi {{client_name}}, resume: {{session_link}}",
        "variables": ["client_name", "session_link", "stage"],
    },
]


async def seed_tenant() -> None:
    if await Tenant.find_one(Tenant.slug == "default"):
        return
    await Tenant(slug="default", name="Default Organization", plan="enterprise", status="active").insert()
    logger.info("Seeded default tenant")


async def seed_ai_config() -> None:
    from app.services.ai_config_service import get_or_create_ai_config

    if await AiConfig.find_one(AiConfig.tenant_id == "default"):
        return
    await get_or_create_ai_config("default")
    logger.info("Seeded AI config")


async def seed_system_config() -> None:
    if await SystemConfig.find_one(SystemConfig.tenant_id == "default"):
        return
    await SystemConfig(
        tenant_id="default",
        max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB,
        max_files_per_session=settings.MAX_FILES_PER_SESSION,
        product_name="Client Onboarding Agent",
        support_email=settings.ATI_SUPPORT_EMAIL,
        privacy_url=settings.ATI_PRIVACY_URL,
        phone=settings.ATI_PHONE,
    ).insert()
    logger.info("Seeded system config")


async def migrate_role_sort_order() -> None:
    order_map = {"Super Admin": 1, "Admin": 2, "User": 3}
    changed = 0
    for role in await Role.find_all().to_list():
        expected = order_map.get(role.name, 99)
        if role.sort_order != expected:
            role.sort_order = expected
            await role.save()
            changed += 1
    if changed:
        logger.info("Migrated sort_order on %d roles", changed)


async def ensure_page_actions(page_name: str) -> None:
    now = datetime.now(timezone.utc)
    for action_name, action_key in ACTION_KEYS:
        existing = await ApplicationAction.find_one(
            ApplicationAction.page_name == page_name,
            ApplicationAction.action_key == action_key,
        )
        if not existing:
            await ApplicationAction(
                page_name=page_name,
                action_name=action_name,
                action_key=action_key,
                is_active=True,
                created_by=SYSTEM_CREATOR,
                created_at=now,
                updated_at=now,
            ).insert()


async def merge_role_permissions_for_page(module_name: str, page_name: str) -> None:
    for role_name in ("Super Admin", "Admin"):
        role = await Role.find_one(Role.name == role_name)
        if not role:
            continue
        perms = role.permissions or {}
        perms.setdefault(module_name, {})
        if page_name not in perms[module_name]:
            perms[module_name][page_name] = {
                "view": True,
                "insert": True,
                "update": True,
                "delete": True,
            }
            role.permissions = perms
            await role.save()


async def seed_tenant_defaults(tenant_id: str) -> None:
    from app.services.ai_config_service import get_or_create_ai_config

    if not await AiConfig.find_one(AiConfig.tenant_id == tenant_id):
        await get_or_create_ai_config(tenant_id)
    if not await SystemConfig.find_one(SystemConfig.tenant_id == tenant_id):
        await SystemConfig(
            tenant_id=tenant_id,
            max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB,
            max_files_per_session=settings.MAX_FILES_PER_SESSION,
            product_name="Client Onboarding Agent",
            support_email=settings.ATI_SUPPORT_EMAIL,
            privacy_url=settings.ATI_PRIVACY_URL,
            phone=settings.ATI_PHONE,
        ).insert()
    now = datetime.now(timezone.utc)
    for tpl in DEFAULT_EMAIL_TEMPLATES:
        if not await EmailTemplate.find_one(
            EmailTemplate.tenant_id == tenant_id,
            EmailTemplate.key == tpl["key"],
        ):
            await EmailTemplate(tenant_id=tenant_id, updated_at=now, **tpl).insert()
    if not await FollowUpRule.find_one(FollowUpRule.tenant_id == tenant_id):
        await FollowUpRule(
            tenant_id=tenant_id,
            trigger="session_idle",
            delay_hours=24,
            template_key="session_reminder",
            is_active=True,
            max_sends=3,
        ).insert()


async def migrate_config_pages() -> None:
    """Ensure config/SaaS pages exist for existing deployments."""
    now = datetime.now(timezone.utc)
    new_pages = [
        {"module_name": "Configuration", "page_name": "AI Configuration", "route": "/admin/config-ai.html", "sort_order": 1},
        {"module_name": "Configuration", "page_name": "System Configuration", "route": "/admin/config-system.html", "sort_order": 2},
        {"module_name": "Configuration", "page_name": "Workspace", "route": "/admin/config-tenant.html", "sort_order": 6},
        {"module_name": "Configuration", "page_name": "API Keys", "route": "/admin/config-api-keys.html", "sort_order": 7},
        {"module_name": "Configuration", "page_name": "Usage & Limits", "route": "/admin/config-usage.html", "sort_order": 8},
        {"module_name": "Settings", "page_name": "Audit Log", "route": "/admin/settings-audit.html", "sort_order": 6},
    ]
    for page_def in new_pages:
        existing = await ApplicationPage.find_one(
            ApplicationPage.route == page_def["route"]
        )
        if not existing:
            await ApplicationPage(
                **page_def,
                is_active=True,
                created_by=SYSTEM_CREATOR,
                created_at=now,
                updated_at=now,
            ).insert()
            logger.info("Added page: %s", page_def["page_name"])
        await ensure_page_actions(page_def["page_name"])
        await merge_role_permissions_for_page(page_def["module_name"], page_def["page_name"])


async def seed_email_templates() -> None:
    if await EmailTemplate.find_one(EmailTemplate.tenant_id == "default"):
        return
    now = datetime.now(timezone.utc)
    for tpl in DEFAULT_EMAIL_TEMPLATES:
        await EmailTemplate(tenant_id="default", updated_at=now, **tpl).insert()
    logger.info("Seeded email templates")


async def seed_follow_up_rules() -> None:
    if await FollowUpRule.find_one(FollowUpRule.tenant_id == "default"):
        return
    await FollowUpRule(
        tenant_id="default",
        trigger="session_idle",
        delay_hours=24,
        template_key="session_reminder",
        is_active=True,
        max_sends=3,
    ).insert()
    logger.info("Seeded follow-up rules")


async def migrate_tenant_ids() -> None:
    changed = 0
    for model, field in [
        (User, "tenant_id"),
        (OnboardingSessionDoc, "tenant_id"),
        (Brief, "tenant_id"),
        (SmtpConfig, "tenant_id"),
    ]:
        docs = await model.find_all().to_list()
        for doc in docs:
            if not getattr(doc, field, None):
                setattr(doc, field, "default")
                await doc.save()
                changed += 1
    if changed:
        logger.info("Backfilled tenant_id on %d documents", changed)


async def migrate_existing_users() -> None:
    users = await User.find_all().to_list()
    changed = 0
    for user in users:
        updated = False
        if user.role == "admin" and user.email == settings.ADMIN_EMAIL.lower():
            if not user.is_super_admin:
                user.is_super_admin = True
                user.role_name = "Super Admin"
                updated = True
        elif not user.role_name:
            user.role_name = "Admin" if user.role == "admin" else "User"
            updated = True
        if not user.tenant_id:
            user.tenant_id = "default"
            updated = True
        if updated:
            await user.save()
            changed += 1
    if changed:
        logger.info("Migrated %d users", changed)


async def run_all_seeders() -> None:
    await seed_tenant()
    await seed_modules()
    await seed_pages()
    await seed_actions()
    await seed_roles()
    await seed_ai_config()
    await seed_system_config()
    await seed_email_templates()
    await seed_follow_up_rules()
    await migrate_role_sort_order()
    await migrate_config_pages()
    await migrate_tenant_ids()
    await migrate_existing_users()
    await warm_config_cache("default")
    await warm_ai_config_cache("default")
