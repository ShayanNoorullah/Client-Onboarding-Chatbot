import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api.admin_routes import router as admin_router
from app.api.auth_routes import router as auth_router
from app.api.brief_routes import router as brief_router
from app.api.routes import router as chat_router
from app.api.user_routes import router as user_router
from app.config import settings
from app.db.mongodb import close_mongodb, connect_mongodb, seed_admin_user
from app.llm.factory import check_ollama_health

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_mongodb()
    await seed_admin_user()
    yield
    await close_mongodb()


app = FastAPI(title="ATI Onboarding Chatbot", version="3.0.0", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET_KEY)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(brief_router)
app.include_router(chat_router)


@app.get("/health")
async def health():
    ollama = check_ollama_health()
    status = "ok" if ollama["ollama_reachable"] and not ollama["missing"] else "degraded"
    return {
        "status": status,
        "service": "ATI Onboarding Bot",
        "version": "3.0.0",
        "llm_provider": "ollama",
        "ollama": ollama,
    }


STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static_assets")
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
