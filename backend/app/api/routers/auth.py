"""Authentication and profile management."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import schemas
from app.api.deps import current_user, db, log_action
from app.core.security import hash_password, make_token, verify_password
from app.database.models import User, UserSettings

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "phone": user.phone or "",
        "profile_image": user.profile_image or "",
        "blood_group": user.blood_group or "",
        "date_of_birth": user.date_of_birth or "",
        "gender": user.gender or "",
        "address": user.address or "",
        "emergency_contact": user.emergency_contact or "",
        "is_verified": bool(user.is_verified),
        "is_active": bool(user.is_active),
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _token_payload(user: User) -> dict:
    return {
        "access_token": make_token(user.id, user.role),
        "token_type": "bearer",
        "role": user.role,
        "name": user.name,
        "user": _user_payload(user),
    }


@router.post("/register")
def register(body: schemas.RegisterIn, s: Session = Depends(db)):
    email = body.email.strip().lower()
    if s.query(User).filter_by(email=email).first():
        raise HTTPException(409, "Email already registered")

    user = User(
        email=email,
        name=body.name.strip(),
        role=body.role,
        password_hash=hash_password(body.password),
    )
    s.add(user)
    s.commit()
    s.refresh(user)

    # Every account gets a settings row so the UI never has to invent defaults.
    s.add(UserSettings(user_id=user.id))
    s.commit()
    log_action(s, user.id, f"user_registered:{user.role}")
    return _token_payload(user)


@router.post("/login")
def login(body: schemas.LoginIn, s: Session = Depends(db)):
    user = s.query(User).filter_by(email=body.email.strip().lower()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(403, "This account has been deactivated")
    log_action(s, user.id, "user_login")
    return _token_payload(user)


@router.get("/me")
def me(user: User = Depends(current_user)):
    return _user_payload(user)


@router.put("/me")
def update_me(
    body: schemas.ProfileUpdateIn,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    data = body.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    user.updated_at = datetime.utcnow()
    s.commit()
    s.refresh(user)
    log_action(s, user.id, "profile_updated")
    return _user_payload(user)


@router.post("/change-password")
def change_password(
    body: schemas.ChangePasswordIn,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(401, "Current password is incorrect")
    if body.current_password == body.new_password:
        raise HTTPException(422, "The new password must differ from the current one")
    user.password_hash = hash_password(body.new_password)
    user.updated_at = datetime.utcnow()
    s.commit()
    log_action(s, user.id, "password_changed")
    return {"status": "ok", "message": "Password updated. Sign in again on other devices."}


@router.get("/providers")
def providers():
    """Secret-free view of which AI provider is active."""
    from app.services.ai_service import availability

    return availability()
