import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.llm.factory import check_ollama_health

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = FastAPI(title="ATI Onboarding Chatbot", version="2.0.0")
app.include_router(router)


@app.get("/health")
async def health():
    ollama = check_ollama_health()
    status = "ok" if ollama["ollama_reachable"] and not ollama["missing"] else "degraded"
    return {
        "status": status,
        "service": "ATI Onboarding Bot",
        "llm_provider": "ollama",
        "ollama": ollama,
    }


FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"
LEGACY_STATIC = Path(__file__).parent / "static"

if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
elif LEGACY_STATIC.exists():
    app.mount("/static", StaticFiles(directory=LEGACY_STATIC), name="static")
