import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api.admin_routes import router as admin_router
from app.api.auth_routes import router as auth_router
from app.api.config_routes import router as config_router
from app.api.settings_routes import router as settings_router
from app.api.audit_routes import router as audit_router
from app.api.notification_routes import router as notification_router
from app.api.portal_routes import router as portal_router
from app.api.signature_routes import router as signature_router
from app.api.tenant_routes import router as tenant_router
from app.api.webhook_routes import router as webhook_router
from app.middleware.tenant import TenantMiddleware
from app.services.follow_up_scheduler import start_follow_up_scheduler
from app.services.learning_scheduler import start_learning_scheduler
from app.services.ai_config_service import warm_ai_config_cache
from app.services.system_config_service import warm_config_cache
from app.api.brief_routes import router as brief_router
from app.api.learning_routes import router as learning_router
from app.api.public_routes import router as public_router
from app.api.routes import router as chat_router
from app.api.user_routes import router as user_router
from app.config import settings
from app.db.mongodb import close_mongodb, connect_mongodb, seed_admin_user
from app.llm.factory import check_ollama_health

_log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(level=_log_level, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_mongodb()
    await seed_admin_user()
    await warm_config_cache("default")
    await warm_ai_config_cache("default")
    start_follow_up_scheduler()
    start_learning_scheduler()
    yield
    await close_mongodb()


app = FastAPI(title="Client Onboarding Agent", version="3.2.0", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET_KEY)
app.add_middleware(TenantMiddleware)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(settings_router, prefix="/api/admin")
app.include_router(config_router, prefix="/api/admin")
app.include_router(tenant_router)
app.include_router(audit_router)
app.include_router(webhook_router)
app.include_router(notification_router)
app.include_router(portal_router)
app.include_router(signature_router)
app.include_router(brief_router)
app.include_router(public_router)
app.include_router(chat_router)
app.include_router(learning_router)


@app.get("/health")
async def health():
    ollama = check_ollama_health()
    status = "ok" if ollama["ollama_reachable"] and not ollama["missing"] else "degraded"
    return {
        "status": status,
        "service": "Client Onboarding Agent",
        "version": "3.2.0",
        "llm_provider": "ollama",
        "ollama": ollama,
    }


STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static_assets")
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
