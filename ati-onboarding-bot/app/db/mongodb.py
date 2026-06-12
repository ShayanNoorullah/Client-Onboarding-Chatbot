import logging

from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.config import settings
from app.db.seeders import run_all_seeders
from app.models.api_key import ApiKey
from app.models.app_action import ApplicationAction
from app.models.app_module import ApplicationModule
from app.models.app_page import ApplicationPage
from app.models.audit_event import AuditEvent
from app.models.brief import Brief
from app.models.brief_feedback import BriefFeedback
from app.models.email_template import EmailTemplate
from app.models.follow_up_rule import FollowUpRule
from app.models.onboarding_session import OnboardingSessionDoc
from app.models.role import Role
from app.models.smtp_config import SmtpConfig
from app.models.ai_config import AiConfig
from app.models.system_config import SystemConfig
from app.models.tenant import Tenant
from app.models.usage_record import UsageRecord
from app.models.user import User
from app.models.user_memory import UserMemory

logger = logging.getLogger(__name__)

_client: AsyncMongoClient | None = None


async def connect_mongodb() -> None:
    global _client
    # Beanie 2.x requires PyMongo AsyncMongoClient (Motor is incompatible).
    _client = AsyncMongoClient(settings.MONGODB_URI)
    await init_beanie(
        database=_client[settings.MONGODB_DB_NAME],
        document_models=[
            Tenant,
            User,
            OnboardingSessionDoc,
            Brief,
            BriefFeedback,
            UserMemory,
            Role,
            ApplicationModule,
            ApplicationPage,
            ApplicationAction,
            SmtpConfig,
            AiConfig,
            SystemConfig,
            EmailTemplate,
            FollowUpRule,
            AuditEvent,
            ApiKey,
            UsageRecord,
        ],
    )
    await run_all_seeders()
    logger.info("Connected to MongoDB: %s", settings.MONGODB_DB_NAME)


async def close_mongodb() -> None:
    global _client
    if _client:
        await _client.aclose()
        _client = None
        logger.info("MongoDB connection closed")


async def seed_admin_user() -> None:
    from app.auth.passwords import hash_password

    existing = await User.find_one(User.role == "admin")
    if existing:
        return
    admin = User(
        email=settings.ADMIN_EMAIL.lower(),
        password_hash=hash_password(settings.ADMIN_PASSWORD),
        full_name=settings.ADMIN_FULL_NAME,
        role="admin",
        role_name="Super Admin",
        is_super_admin=True,
        tenant_id="default",
        is_active=True,
    )
    await admin.insert()
    logger.info("Seeded admin user: %s", settings.ADMIN_EMAIL)
