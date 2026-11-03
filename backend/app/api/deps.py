"""Shared FastAPI dependencies: database session, authentication and audit logging."""
from __future__ import annotations

from datetime import datetime

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import SessionLocal
from app.database.models import AuditLog, User


def db():
    """Yield a SQLAlchemy session and always close it.

    Kept importable from ``app.main`` for existing tests that override it.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=401, detail=detail, headers={"WWW-Authenticate": "Bearer"}
    )


def current_user(
    authorization: str | None = Header(default=None), s: Session = Depends(db)
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized("Authentication required")
    try:
        payload = decode_token(authorization.split(" ", 1)[1])
        user_id = int(payload["sub"])
    except Exception:
        raise _unauthorized("Invalid or expired token")
    user = s.get(User, user_id)
    if not user:
        raise _unauthorized("User no longer exists")
    if not user.is_active:
        raise HTTPException(403, "This account has been deactivated")
    return user


def require(*roles: str):
    """Role gate. ``require()`` with no roles means "any authenticated user"."""

    def dependency(user: User = Depends(current_user)) -> User:
        if roles and user.role not in roles:
            raise HTTPException(403, "Insufficient permissions")
        return user

    return dependency


def log_action(s: Session, user_id: int | None, action: str, commit: bool = True) -> None:
    """Append an audit entry. Never stores report contents or credentials."""
    s.add(AuditLog(user_id=user_id, action=action[:160], at=datetime.utcnow()))
    if commit:
        s.commit()


def notify(
    s: Session,
    user_id: int,
    title: str,
    message: str = "",
    type: str = "info",
    commit: bool = True,
) -> None:
    """Create an in-app notification for a user."""
    from app.database.models import Notification

    s.add(
        Notification(
            user_id=user_id, title=title[:255], message=message, type=type
        )
    )
    if commit:
        s.commit()
