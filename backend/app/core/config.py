"""
MediSense – centralised configuration.

All settings are read from environment variables (with sensible defaults for dev).
Secrets are never sent to the browser: only ``/api/meta`` exposes *whether* a
provider is configured, never the key itself.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# ── Project root: backend/ ────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def _flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


# ── Database ──────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{(BASE_DIR / 'medisense.db').as_posix()}",
)

# ── Security ──────────────────────────────────────────────────────────
SECRET_KEY: str = os.getenv(
    "SECRET_KEY", "CHANGE_THIS_DEVELOPMENT_SECRET_BEFORE_DEPLOYMENT"
)
ACCESS_TOKEN_TTL_SECONDS: int = int(os.getenv("ACCESS_TOKEN_TTL_SECONDS", str(8 * 3600)))
SECRET_KEY_IS_DEFAULT: bool = SECRET_KEY.startswith("CHANGE_THIS")

# ── AI providers ──────────────────────────────────────────────────────
# demo   → deterministic, clearly labelled educational answers (no LLM call)
# gemini → Google Gemini generateContent API
# openai → OpenAI chat completions API
AI_PROVIDER: str = os.getenv("AI_PROVIDER", "demo").strip().lower()
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
AI_TIMEOUT_SECONDS: float = float(os.getenv("AI_TIMEOUT_SECONDS", "45"))
AI_MAX_HISTORY: int = int(os.getenv("AI_MAX_HISTORY", "12"))


def provider_status() -> dict:
    """Report provider configuration without leaking any secret material."""
    configured = {
        "demo": True,
        "gemini": bool(GEMINI_API_KEY),
        "openai": bool(OPENAI_API_KEY),
    }
    active = AI_PROVIDER if AI_PROVIDER in configured else "demo"
    # A provider requested without a key must never silently pretend to be live.
    effective = active if configured.get(active) else "demo"
    return {
        "requested": AI_PROVIDER,
        "active": effective,
        "live": effective != "demo",
        "configured": configured,
        "model": GEMINI_MODEL if effective == "gemini" else OPENAI_MODEL if effective == "openai" else None,
        "detail": None
        if configured.get(active)
        else f"AI_PROVIDER={AI_PROVIDER} requested but no API key is configured; "
        "falling back to labelled demo mode.",
    }


# ── File uploads ──────────────────────────────────────────────────────
UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))
MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
ALLOWED_REPORT_TYPES: tuple[str, ...] = (
    "application/pdf",
    "application/octet-stream",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/tiff",
)
ALLOWED_IMAGE_EXTENSIONS: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff")

# ── CORS ──────────────────────────────────────────────────────────────
CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,https://localhost",
    ).split(",")
    if origin.strip()
]

# ── Runtime ───────────────────────────────────────────────────────────
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
FRONTEND_DIST: Path = Path(
    os.getenv("FRONTEND_DIST", str(BASE_DIR.parent / "frontend" / "dist"))
)
SERVE_FRONTEND: bool = _flag("SERVE_FRONTEND", "true")

