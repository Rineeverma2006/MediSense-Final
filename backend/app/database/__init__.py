"""
MediSense – database engine, session factory, declarative base, and get_db dependency.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    """FastAPI dependency – yields a SQLAlchemy session and closes it afterwards."""
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
