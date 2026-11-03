"""
MediSense – database engine, session factory, declarative base, and get_db dependency.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import DATABASE_URL

database_url = DATABASE_URL
connect_args = {}
engine_options = {"future": True, "pool_pre_ping": True}

if database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
elif database_url.startswith(("postgres://", "postgresql://")):
    # Supabase's transaction pooler is the right fit for short-lived serverless
    # requests. Use psycopg 3 and disable prepared statements for PgBouncer.
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    connect_args["prepare_threshold"] = None
    engine_options.update(pool_size=1, max_overflow=0, pool_recycle=300)

engine = create_engine(database_url, connect_args=connect_args, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    """FastAPI dependency – yields a SQLAlchemy session and closes it afterwards."""
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

