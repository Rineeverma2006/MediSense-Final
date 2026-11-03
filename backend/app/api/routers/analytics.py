"""Analytics and administrator endpoints — all computed from real DB rows."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import schemas
from app.api.deps import current_user, db, log_action, require
from app.database.models import (
    Appointment,
    AuditLog,
    Conversation,
    Doctor,
    HealthMetric,
    HealthRecord,
    Medication,
    Notification,
    Report,
    SupportTicket,
    User,
    WearableDevice,
)

router = APIRouter(tags=["analytics"])


# ══════════════════════════════════════════════════════════════════════
# Patient analytics
# ══════════════════════════════════════════════════════════════════════
@router.get("/api/analytics/summary")
def analytics_summary(user: User = Depends(current_user), s: Session = Depends(db)):
    report_count = s.query(Report).filter_by(user_id=user.id).count()
    appointment_count = s.query(Appointment).filter_by(user_id=user.id).count()
    active_meds = s.query(Medication).filter_by(user_id=user.id, active=True).count()
    metric_count = s.query(HealthMetric).filter_by(user_id=user.id).count()

    flagged_total = 0
    for report in s.query(Report).filter_by(user_id=user.id).all():
        import json

        try:
            flagged_total += int(json.loads(report.analysis_json).get("counts", {}).get("flagged", 0))
        except (ValueError, TypeError):
            continue

    upcoming = (
        s.query(Appointment)
        .filter(Appointment.user_id == user.id, Appointment.status == "scheduled")
        .count()
    )
    unread_count = (
        s.query(Notification).filter_by(user_id=user.id, is_read=False).count()
    )

    return {
        "reports": report_count,
        "appointments": appointment_count,
        "active_medications": active_meds,
        "metrics": metric_count,
        "flagged_parameters": flagged_total,
        "upcoming_appointments": upcoming,
        "unread_notifications": unread_count,
        "health_records": s.query(HealthRecord).filter_by(user_id=user.id).count(),
        "wearables": s.query(WearableDevice).filter_by(user_id=user.id).count(),
        "conversations": s.query(Conversation).filter_by(user_id=user.id).count(),
        "data_source": "database",
    }


@router.get("/api/analytics/health-summary")
def health_summary(user: User = Depends(current_user), s: Session = Depends(db)):
    """Per-metric latest value plus trend vs the previous reading."""
    rows = (
        s.query(HealthMetric)
        .filter_by(user_id=user.id)
        .order_by(HealthMetric.id.asc())
        .all()
    )
    grouped: dict[str, list[HealthMetric]] = {}
    for row in rows:
        grouped.setdefault(row.metric, []).append(row)

    summary = []
    for metric, values in grouped.items():
        latest = values[-1]
        previous = values[-2] if len(values) > 1 else None
        delta = round(latest.value - previous.value, 3) if previous else None
        summary.append(
            {
                "metric": metric,
                "unit": latest.unit or "",
                "latest": latest.value,
                "previous": previous.value if previous else None,
                "delta": delta,
                "direction": "flat"
                if delta in (None, 0)
                else ("up" if delta > 0 else "down"),
                "readings": len(values),
                "recorded_at": latest.recorded_at,
                "series": [
                    {"value": v.value, "recorded_at": v.recorded_at} for v in values[-30:]
                ],
            }
        )
    summary.sort(key=lambda x: x["metric"])
    return {"metrics": summary, "tracked": len(summary), "data_source": "database"}


@router.get("/api/analytics/timeline")
def timeline(
    limit: int = 50,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    events: list[dict] = []

    for report in s.query(Report).filter_by(user_id=user.id).all():
        events.append(
            {
                "type": "report",
                "title": f"Report analysed: {report.filename}",
                "at": report.created_at.isoformat(),
                "ref_id": report.id,
            }
        )
    for appointment in s.query(Appointment).filter_by(user_id=user.id).all():
        events.append(
            {
                "type": "appointment",
                "title": f"{appointment.doctor_name} · {appointment.specialty} ({appointment.status})",
                "at": appointment.appointment_at,
                "ref_id": appointment.id,
            }
        )
    for med in s.query(Medication).filter_by(user_id=user.id).all():
        events.append(
            {
                "type": "medication",
                "title": f"Medication {'active' if med.active else 'inactive'}: {med.name}",
                "at": med.created_at.isoformat(),
                "ref_id": med.id,
            }
        )
    for record in s.query(HealthRecord).filter_by(user_id=user.id).all():
        events.append(
            {
                "type": "record",
                "title": f"Health record: {record.title}",
                "at": record.created_at.isoformat(),
                "ref_id": record.id,
            }
        )

    events.sort(key=lambda e: e["at"] or "", reverse=True)
    return events[: max(1, min(limit, 200))]


@router.get("/api/analytics/report-trends")
def report_trends(user: User = Depends(current_user), s: Session = Depends(db)):
    """Flagged-parameter counts per analysed report, oldest first, for charting."""
    import json

    rows = (
        s.query(Report)
        .filter_by(user_id=user.id)
        .order_by(Report.created_at.asc())
        .all()
    )
    points = []
    for report in rows:
        try:
            payload = json.loads(report.analysis_json)
        except (ValueError, TypeError):
            continue
        counts = payload.get("counts", {})
        points.append(
            {
                "report_id": report.id,
                "filename": report.filename,
                "created_at": report.created_at.isoformat(),
                "total": counts.get("total", 0),
                "flagged": counts.get("flagged", 0),
                "within_range": counts.get("within_range", 0),
            }
        )
    return {"points": points, "count": len(points)}


# ══════════════════════════════════════════════════════════════════════
# Administrator analytics
# ══════════════════════════════════════════════════════════════════════
@router.get("/api/admin/stats")
def admin_stats(user: User = Depends(require("admin")), s: Session = Depends(db)):
    since = datetime.utcnow() - timedelta(days=7)
    role_rows = s.query(User.role, func.count(User.id)).group_by(User.role).all()
    status_rows = (
        s.query(Appointment.status, func.count(Appointment.id))
        .group_by(Appointment.status)
        .all()
    )
    return {
        "users": s.query(User).count(),
        "patients": s.query(User).filter_by(role="patient").count(),
        "doctors": s.query(User).filter_by(role="doctor").count(),
        "admins": s.query(User).filter_by(role="admin").count(),
        "reports": s.query(Report).count(),
        "appointments": s.query(Appointment).count(),
        "medications": s.query(Medication).count(),
        "metrics": s.query(HealthMetric).count(),
        "conversations": s.query(Conversation).count(),
        "support_tickets": s.query(SupportTicket).count(),
        "open_tickets": s.query(SupportTicket).filter(SupportTicket.status != "closed").count(),
        "directory_doctors": s.query(Doctor).count(),
        "wearables": s.query(WearableDevice).count(),
        "new_users_7d": s.query(User).filter(User.created_at >= since).count(),
        "by_role": {role: count for role, count in role_rows},
        "appointments_by_status": {status: count for status, count in status_rows},
        "data_source": "database",
    }


def _admin_user_row(u: User) -> dict:
    return {
        "id": u.id,
        "email": u.email,
        "name": u.name,
        "role": u.role,
        "is_active": bool(u.is_active),
        "is_verified": bool(u.is_verified),
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


@router.get("/api/admin/users")
def admin_users(
    role: str | None = None,
    search: str | None = None,
    user: User = Depends(require("admin")),
    s: Session = Depends(db),
):
    query = s.query(User)
    if role:
        query = query.filter(User.role == role)
    if search:
        like = f"%{search.strip()}%"
        query = query.filter((User.email.ilike(like)) | (User.name.ilike(like)))
    rows = query.order_by(User.id.desc()).limit(500).all()
    return [_admin_user_row(u) for u in rows]


@router.patch("/api/admin/users/{user_id}/role")
def admin_set_role(
    user_id: int,
    body: schemas.RoleIn,
    user: User = Depends(require("admin")),
    s: Session = Depends(db),
):
    target = s.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")
    if target.id == user.id:
        raise HTTPException(422, "You cannot change your own role")
    target.role = body.role
    target.updated_at = datetime.utcnow()
    s.commit()
    log_action(s, user.id, f"role_changed:{user_id}:{body.role}")
    return _admin_user_row(target)


@router.patch("/api/admin/users/{user_id}/active")
def admin_set_active(
    user_id: int,
    user: User = Depends(require("admin")),
    s: Session = Depends(db),
):
    target = s.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")
    if target.id == user.id:
        raise HTTPException(422, "You cannot deactivate your own account")
    target.is_active = not bool(target.is_active)
    target.updated_at = datetime.utcnow()
    s.commit()
    log_action(s, user.id, f"user_active_toggle:{user_id}:{target.is_active}")
    return _admin_user_row(target)


@router.get("/api/admin/audit")
def admin_audit(user: User = Depends(require("admin")), s: Session = Depends(db)):
    rows = s.query(AuditLog).order_by(AuditLog.at.desc()).limit(200).all()
    return [
        {"user_id": a.user_id, "action": a.action, "at": a.at.isoformat()} for a in rows
    ]


@router.get("/api/admin/activity")
def admin_activity(user: User = Depends(require("admin")), s: Session = Depends(db)):
    """Action counts over the last 7 days, derived from the audit log."""
    since = datetime.utcnow() - timedelta(days=7)
    rows = s.query(AuditLog).filter(AuditLog.at >= since).all()
    counter = Counter(a.action.split(":")[0] for a in rows)
    return {
        "window_days": 7,
        "total_events": len(rows),
        "by_action": dict(counter.most_common(15)),
    }
