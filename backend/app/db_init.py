"""Database initialisation and demo seeding.

``init_db()`` applies Alembic migrations instead of relying on
``Base.metadata.create_all``. If the schema was already created by an older
release (tables exist but there is no ``alembic_version``), the current
revision is stamped first so the upgrade does not attempt to recreate tables.
Any failure falls back to ``create_all`` so the API still starts in a bare
development sandbox, with a warning logged.
"""
from __future__ import annotations

import logging

from sqlalchemy import inspect

from app.core.config import BASE_DIR, DATABASE_URL
from app.database import Base, engine

logger = logging.getLogger("medisense.db")

ALEMBIC_INI = BASE_DIR / "alembic.ini"
MIGRATIONS_DIR = BASE_DIR / "migrations"


def init_db() -> str:
    """Bring the database up to ``head``. Returns the strategy that succeeded."""
    try:
        from alembic import command
        from alembic.config import Config

        if not ALEMBIC_INI.is_file():
            raise FileNotFoundError(f"alembic.ini not found at {ALEMBIC_INI}")

        config = Config(str(ALEMBIC_INI))
        config.set_main_option("script_location", str(MIGRATIONS_DIR))
        config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))

        tables = set(inspect(engine).get_table_names())
        legacy_schema = "users" in tables and "alembic_version" not in tables
        if legacy_schema:
            logger.warning(
                "Existing schema without alembic history detected; stamping head "
                "before upgrade."
            )
            command.stamp(config, "head")

        command.upgrade(config, "head")
        logger.info("Database migrated to head.")
        return "alembic"
    except Exception as exc:  # noqa: BLE001 - startup must not hard-fail
        logger.warning("Alembic upgrade failed (%s); falling back to create_all.", exc)
        Base.metadata.create_all(bind=engine)
        return "create_all"


# ── Demo directory data ───────────────────────────────────────────────
# Clearly flagged with ``is_demo=True``: these are illustrative directory
# entries, not verified practitioners, and the UI labels them as sample data.
DEMO_DOCTORS = [
    {
        "name": "Dr. Aarav Mehta",
        "specialty": "Cardiology",
        "qualification": "MBBS, MD (Cardiology)",
        "experience": "14 years",
        "hospital": "Sunrise Heart Institute",
        "rating": 4.8,
        "consultation_fee": 900.0,
        "about": "Interventional cardiologist focused on preventive heart health "
        "and post-procedure rehabilitation.",
    },
    {
        "name": "Dr. Priya Nair",
        "specialty": "Endocrinology",
        "qualification": "MBBS, DM (Endocrinology)",
        "experience": "11 years",
        "hospital": "Metro Diabetes Centre",
        "rating": 4.7,
        "consultation_fee": 800.0,
        "about": "Diabetes and thyroid specialist working with continuous glucose "
        "monitoring and lifestyle-led care.",
    },
    {
        "name": "Dr. Daniel Osei",
        "specialty": "General Physician",
        "qualification": "MBBS, MRCGP",
        "experience": "9 years",
        "hospital": "City Care Clinic",
        "rating": 4.6,
        "consultation_fee": 500.0,
        "about": "Primary care physician handling routine screening, vaccinations "
        "and chronic disease follow-up.",
    },
    {
        "name": "Dr. Sofia Alvarez",
        "specialty": "Dermatology",
        "qualification": "MBBS, MD (Dermatology)",
        "experience": "8 years",
        "hospital": "ClearSkin Dermatology",
        "rating": 4.5,
        "consultation_fee": 700.0,
        "about": "Clinical dermatologist treating acne, eczema and pigmentation "
        "with evidence-based protocols.",
    },
    {
        "name": "Dr. Kenji Tanaka",
        "specialty": "Neurology",
        "qualification": "MBBS, DM (Neurology)",
        "experience": "16 years",
        "hospital": "Northside Neuro Hospital",
        "rating": 4.9,
        "consultation_fee": 1100.0,
        "about": "Neurologist specialising in migraine, epilepsy and stroke "
        "recovery programmes.",
    },
    {
        "name": "Dr. Amina Haddad",
        "specialty": "Paediatrics",
        "qualification": "MBBS, MD (Paediatrics)",
        "experience": "12 years",
        "hospital": "Little Steps Children's Clinic",
        "rating": 4.8,
        "consultation_fee": 650.0,
        "about": "Paediatrician covering growth monitoring, immunisation schedules "
        "and childhood asthma.",
    },
    {
        "name": "Dr. Lucas Meyer",
        "specialty": "Orthopaedics",
        "qualification": "MBBS, MS (Orthopaedics)",
        "experience": "13 years",
        "hospital": "Motion Orthopaedic Centre",
        "rating": 4.4,
        "consultation_fee": 950.0,
        "about": "Joint and sports-injury specialist with a rehabilitation-first "
        "approach.",
    },
    {
        "name": "Dr. Hannah Cole",
        "specialty": "Psychiatry",
        "qualification": "MBBS, MD (Psychiatry)",
        "experience": "10 years",
        "hospital": "MindWell Clinic",
        "rating": 4.7,
        "consultation_fee": 850.0,
        "about": "Adult psychiatrist supporting anxiety, depression and sleep "
        "disorders alongside therapy.",
    },
]


def seed_demo_data() -> dict:
    """Insert demo directory doctors if the directory is empty.

    Idempotent. Never creates user accounts or patient records.
    """
    from app.database import SessionLocal
    from app.database.models import Doctor

    session = SessionLocal()
    try:
        existing = session.query(Doctor).count()
        if existing:
            return {"doctors_inserted": 0, "existing_doctors": existing}
        for entry in DEMO_DOCTORS:
            session.add(Doctor(**entry, is_active=True, is_demo=True))
        session.commit()
        return {"doctors_inserted": len(DEMO_DOCTORS), "existing_doctors": existing}
    finally:
        session.close()
