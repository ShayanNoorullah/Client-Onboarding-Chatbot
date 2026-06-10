import logging

from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.config import settings
from app.models.brief import Brief
from app.models.onboarding_session import OnboardingSessionDoc
from app.models.user import User

logger = logging.getLogger(__name__)

_client: AsyncMongoClient | None = None


async def connect_mongodb() -> None:
    global _client
    # Beanie 2.x requires PyMongo AsyncMongoClient (Motor is incompatible).
    _client = AsyncMongoClient(settings.MONGODB_URI)
    await init_beanie(
        database=_client[settings.MONGODB_DB_NAME],
        document_models=[User, OnboardingSessionDoc, Brief],
    )
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
        is_active=True,
    )
    await admin.insert()
    logger.info("Seeded admin user: %s", settings.ADMIN_EMAIL)
