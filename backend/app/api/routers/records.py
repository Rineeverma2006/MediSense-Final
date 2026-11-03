"""Health records, notifications and user settings."""
from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import schemas
from app.api.deps import current_user, db, log_action
from app.database.models import HealthRecord, Notification, Report, User, UserSettings

router = APIRouter(tags=["records"])


# ══════════════════════════════════════════════════════════════════════
# Health records
# ══════════════════════════════════════════════════════════════════════
def record_row(r: HealthRecord) -> dict:
    return {
        "id": r.id,
        "title": r.title,
        "record_type": r.record_type or "general",
        "type": r.record_type or "general",
        "date": r.date or "",
        "description": r.description or "",
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.get("/api/health-records")
def list_records(user: User = Depends(current_user), s: Session = Depends(db)):
    """Manual records plus the user's analysed reports, unified chronologically."""
    manual = s.query(HealthRecord).filter_by(user_id=user.id).all()
    rows = [record_row(r) for r in manual]
    reports = (
        s.query(Report).filter_by(user_id=user.id).order_by(Report.created_at.desc()).all()
    )
    for report in reports:
        rows.append(
            {
                "id": f"report-{report.id}",
                "report_id": report.id,
                "title": report.filename,
                "type": "Medical report",
                "record_type": "lab_report",
                "date": report.created_at.isoformat(),
                "description": "Analysed lab report",
                "created_at": report.created_at.isoformat(),
            }
        )
    rows.sort(key=lambda x: x.get("date") or x.get("created_at") or "", reverse=True)
    return rows


@router.post("/api/health-records")
def create_record(
    body: schemas.HealthRecordIn,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    record = HealthRecord(
        user_id=user.id,
        title=body.title,
        record_type=body.record_type,
        date=body.date or datetime.utcnow().date().isoformat(),
        description=body.description,
    )
    s.add(record)
    s.commit()
    s.refresh(record)
    log_action(s, user.id, f"health_record_created:{record.id}")
    return record_row(record)


@router.delete("/api/health-records/{record_id}")
def delete_record(
    record_id: str,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    if record_id.startswith("report-"):
        report_id = record_id.removeprefix("report-")
        report = (
            s.query(Report)
            .filter_by(id=int(report_id), user_id=user.id)
            .first()
            if report_id.isdigit()
            else None
        )
        if not report:
            raise HTTPException(404, "Record not found")
        s.delete(report)
        s.commit()
        return {"status": "deleted", "id": record_id}

    if not record_id.isdigit():
        raise HTTPException(422, "Invalid record id")
    record = s.query(HealthRecord).filter_by(id=int(record_id), user_id=user.id).first()
    if not record:
        raise HTTPException(404, "Record not found")
    s.delete(record)
    s.commit()
    log_action(s, user.id, f"health_record_deleted:{record_id}")
    return {"status": "deleted", "id": record_id}


# ══════════════════════════════════════════════════════════════════════
# Notifications
# ══════════════════════════════════════════════════════════════════════
def notification_row(n: Notification) -> dict:
    return {
        "id": n.id,
        "title": n.title,
        "message": n.message or "",
        "type": n.type or "info",
        "is_read": bool(n.is_read),
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }


@router.get("/api/notifications")
def list_notifications(
    unread_only: bool = False,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    query = s.query(Notification).filter_by(user_id=user.id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    rows = query.order_by(Notification.created_at.desc()).limit(100).all()
    return [notification_row(n) for n in rows]


@router.post("/api/notifications")
def create_notification(
    body: schemas.NotificationIn,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    # Patients may only create notifications for themselves; admin may target others.
    target = user.id
    if body.user_id and body.user_id != user.id:
        if user.role != "admin":
            raise HTTPException(403, "Insufficient permissions")
        target = body.user_id
    n = Notification(
        user_id=target, title=body.title, message=body.message, type=body.type
    )
    s.add(n)
    s.commit()
    s.refresh(n)
    return notification_row(n)


@router.patch("/api/notifications/{notification_id}/read")
def mark_read(
    notification_id: int,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    n = s.query(Notification).filter_by(id=notification_id, user_id=user.id).first()
    if not n:
        raise HTTPException(404, "Notification not found")
    n.is_read = True
    s.commit()
    return notification_row(n)


@router.patch("/api/notifications/read-all")
def mark_all_read(user: User = Depends(current_user), s: Session = Depends(db)):
    updated = (
        s.query(Notification)
        .filter_by(user_id=user.id, is_read=False)
        .update({"is_read": True})
    )
    s.commit()
    return {"status": "ok", "updated": updated}


@router.delete("/api/notifications/{notification_id}")
def delete_notification(
    notification_id: int,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    n = s.query(Notification).filter_by(id=notification_id, user_id=user.id).first()
    if not n:
        raise HTTPException(404, "Notification not found")
    s.delete(n)
    s.commit()
    return {"status": "deleted", "id": notification_id}


# ══════════════════════════════════════════════════════════════════════
# Settings
# ══════════════════════════════════════════════════════════════════════
def settings_row(settings: UserSettings) -> dict:
    return {
        "theme": settings.theme or "system",
        "language": settings.language or "en",
        "notifications_enabled": bool(settings.notifications_enabled),
        "email_notifications": bool(settings.email_notifications),
    }


def _ensure_settings(s: Session, user: User) -> UserSettings:
    settings = s.query(UserSettings).filter_by(user_id=user.id).first()
    if not settings:
        settings = UserSettings(user_id=user.id)
        s.add(settings)
        s.commit()
        s.refresh(settings)
    return settings


@router.get("/api/settings")
def get_settings(user: User = Depends(current_user), s: Session = Depends(db)):
    return settings_row(_ensure_settings(s, user))


@router.put("/api/settings")
def update_settings(
    body: schemas.SettingsIn,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    settings = _ensure_settings(s, user)
    for field, value in body.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(settings, field, value)
    settings.updated_at = datetime.utcnow()
    s.commit()
    s.refresh(settings)
    return settings_row(settings)


# ══════════════════════════════════════════════════════════════════════
# Family members
# ══════════════════════════════════════════════════════════════════════
@router.get("/api/family")
def list_family(user: User = Depends(current_user), s: Session = Depends(db)):
    from app.database.models import FamilyMember

    rows = s.query(FamilyMember).filter_by(user_id=user.id).all()
    return [
        {
            "id": f.id,
            "name": f.name,
            "relationship_type": f.relationship_type or "",
            "date_of_birth": f.date_of_birth or "",
            "blood_group": f.blood_group or "",
            "notes": f.notes or "",
        }
        for f in rows
    ]


@router.post("/api/family")
def add_family(
    body: schemas.FamilyMemberIn,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    from app.database.models import FamilyMember

    member = FamilyMember(user_id=user.id, **body.model_dump())
    s.add(member)
    s.commit()
    s.refresh(member)
    return {"id": member.id, "name": member.name}


@router.delete("/api/family/{member_id}")
def delete_family(
    member_id: int,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    from app.database.models import FamilyMember

    member = s.query(FamilyMember).filter_by(id=member_id, user_id=user.id).first()
    if not member:
        raise HTTPException(404, "Family member not found")
    s.delete(member)
    s.commit()
    return {"status": "deleted", "id": member_id}
