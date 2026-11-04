"""MediSense API application entrypoint.

Routers live in ``app/api/routers``. This module keeps the historical surface:
it exports ``app`` (the FastAPI instance) and ``db`` (the session dependency) so
existing tests and imports keep working.
"""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request

from app.api.deps import db  # re-exported for tests: `from app.main import db`
from app.api.routers import (
    analytics,
    assistant,
    auth,
    clinical,
    doctors,
    records,
    reports,
    support,
    voice,
)
from app.core.config import (
    CORS_ORIGINS,
    ENVIRONMENT,
    FRONTEND_DIST,
    SECRET_KEY_IS_DEFAULT,
    SERVE_FRONTEND,
    UPLOAD_DIR,
)
from app.database.models import Base, engine
from app.db_init import init_db, seed_demo_data
from app.services.ai_service import availability as ai_availability

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("medisense")

SCHEMA_STRATEGY = init_db()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="MediSense API",
    version="2.0.0",
    description=(
        "AI-assisted healthcare platform: patient records, report analysis, "
        "assistant chat, appointments, doctor and administrator workspaces."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    if request.url.scheme == "https":
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    return response


# ── Routers ───────────────────────────────────────────────────────────
for module in (auth, reports, assistant, clinical, records, support, doctors,
               analytics, voice):
    app.include_router(module.router)


# ── Meta / health ─────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "MediSense API",
        "version": "2.0.0",
        "environment": ENVIRONMENT,
        "ai": ai_availability()["mode"],
    }


@app.get("/api/meta")
def meta():
    """Public runtime metadata. Never exposes secrets."""
    from app.services.document_ocr import ocr_status

    warnings = []
    if SECRET_KEY_IS_DEFAULT:
        warnings.append(
            "SECRET_KEY is still the development default. Set a strong SECRET_KEY "
            "before handling real patient data."
        )
    return {
        "app": "MediSense",
        "version": "2.0.0",
        "environment": ENVIRONMENT,
        "ai": ai_availability(),
        "ocr": ocr_status(),
        "features": {
            "pwa": True,
            "voice": True,
            "anatomy3d": True,
            "wearables": "architecture_ready",
            "report_upload": ["pdf", "png", "jpeg", "webp", "tiff", "txt"],
        },
        "warnings": warnings,
    }


# ── Frontend (single-container deployment) ────────────────────────────
if SERVE_FRONTEND and FRONTEND_DIST.is_dir():
    assets = FRONTEND_DIST / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    index_file = FRONTEND_DIST / "index.html"

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        """Serve the SPA shell; API paths must 404 instead of returning HTML."""
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file() and full_path not in {"index.html"}:
            return FileResponse(candidate)
        return FileResponse(index_file)

    logger.info("Serving frontend from %s", FRONTEND_DIST)
elif SERVE_FRONTEND:
    logger.info("No frontend build at %s; API-only mode", FRONTEND_DIST)


@app.on_event("startup")
def _startup_checks() -> None:
    if SECRET_KEY_IS_DEFAULT:
        if ENVIRONMENT.strip().lower() in {"production", "prod"}:
            raise RuntimeError(
                "Refusing to start in production with the development SECRET_KEY. "
                "Configure a unique, high-entropy SECRET_KEY first."
            )
        logger.warning(
            "SECRET_KEY is the development default — set a strong value before "
            "handling real patient data."
        )
    try:
        seeded = seed_demo_data()
        if seeded["doctors_inserted"]:
            logger.info(
                "Seeded %s demo directory doctors (labelled as sample data).",
                seeded["doctors_inserted"],
            )
    except Exception as exc:  # noqa: BLE001 - seeding must never block startup
        logger.warning("Demo seeding skipped: %s", exc)
    if os.getenv("AI_PROVIDER", "demo").lower() != "demo":
        status = ai_availability()
        if not status["live"]:
            logger.warning("AI provider requested but not configured: %s", status["detail"])

