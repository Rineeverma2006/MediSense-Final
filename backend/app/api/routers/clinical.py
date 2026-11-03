"""Appointments, medications and health metrics — all scoped to the current user."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import schemas
from app.api.deps import current_user, db, log_action, notify, require
from app.database.models import Appointment, HealthMetric, Medication, User

router = APIRouter(tags=["clinical"])


# ══════════════════════════════════════════════════════════════════════
# Appointments
# ══════════════════════════════════════════════════════════════════════
def appointment_row(x: Appointment) -> dict:
    return {
        "id": x.id,
        "doctor_name": x.doctor_name,
        "specialty": x.specialty,
        "appointment_at": x.appointment_at,
        "status": x.status,
        "notes": x.notes or "",
        "doctor_id": getattr(x, "doctor_id", None),
        "created_at": x.created_at.isoformat() if x.created_at else None,
    }


@router.get("/api/appointments")
def appointments(user: User = Depends(current_user), s: Session = Depends(db)):
    rows = (
        s.query(Appointment)
        .filter_by(user_id=user.id)
        .order_by(Appointment.appointment_at.desc(), Appointment.id.desc())
        .all()
    )
    return [appointment_row(x) for x in rows]


@router.post("/api/appointments")
def create_appointment(
    body: schemas.AppointmentIn,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    data = body.model_dump()
    if not data.get("appointment_at", "").strip():
        raise HTTPException(422, "Choose an appointment date and time")
    x = Appointment(user_id=user.id, **data)
    s.add(x)
    s.commit()
    s.refresh(x)
    notify(
        s,
        user.id,
        "Appointment requested",
        f"{x.doctor_name} · {x.specialty} · {x.appointment_at}",
        type="reminder",
        commit=False,
    )
    log_action(s, user.id, f"appointment_created:{x.id}", commit=False)
    s.commit()
    return appointment_row(x)


@router.patch("/api/appointments/{item_id}/cancel")
def cancel_appointment(
    item_id: int,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    x = s.query(Appointment).filter_by(id=item_id, user_id=user.id).first()
    if not x:
        raise HTTPException(404, "Appointment not found")
    x.status = "cancelled"
    x.updated_at = datetime.utcnow()
    s.commit()
    log_action(s, user.id, f"appointment_cancelled:{item_id}")
    return appointment_row(x)


@router.patch("/api/appointments/{item_id}/status")
def set_appointment_status(
    item_id: int,
    body: schemas.AppointmentStatusIn,
    user: User = Depends(require("doctor", "admin")),
    s: Session = Depends(db),
):
    x = s.get(Appointment, item_id)
    if not x:
        raise HTTPException(404, "Appointment not found")
    x.status = body.status
    x.updated_at = datetime.utcnow()
    s.commit()
    log_action(s, user.id, f"appointment_status:{item_id}:{body.status}")
    return appointment_row(x)


@router.delete("/api/appointments/{item_id}")
def delete_appointment(
    item_id: int,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    x = s.query(Appointment).filter_by(id=item_id, user_id=user.id).first()
    if not x:
        raise HTTPException(404, "Appointment not found")
    s.delete(x)
    s.commit()
    log_action(s, user.id, f"appointment_deleted:{item_id}")
    return {"status": "deleted", "id": item_id}


# ══════════════════════════════════════════════════════════════════════
# Medications
# ══════════════════════════════════════════════════════════════════════
def medication_row(m: Medication) -> dict:
    return {
        "id": m.id,
        "name": m.name,
        "dosage": m.dosage or "",
        "frequency": m.frequency or "",
        "start_date": m.start_date or "",
        "end_date": m.end_date or "",
        "active": bool(m.active),
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


@router.get("/api/medications")
def medications(user: User = Depends(current_user), s: Session = Depends(db)):
    rows = (
        s.query(Medication)
        .filter_by(user_id=user.id)
        .order_by(Medication.active.desc(), Medication.id.desc())
        .all()
    )
    return [medication_row(m) for m in rows]


@router.post("/api/medications")
def add_medication(
    body: schemas.MedicationIn,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    m = Medication(user_id=user.id, **body.model_dump())
    s.add(m)
    s.commit()
    s.refresh(m)
    log_action(s, user.id, f"medication_created:{m.id}")
    return medication_row(m)


@router.put("/api/medications/{item_id}")
def update_medication(
    item_id: int,
    body: schemas.MedicationUpdateIn,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    m = s.query(Medication).filter_by(id=item_id, user_id=user.id).first()
    if not m:
        raise HTTPException(404, "Medication not found")
    for field, value in body.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(m, field, value)
    m.updated_at = datetime.utcnow()
    s.commit()
    s.refresh(m)
    log_action(s, user.id, f"medication_updated:{item_id}")
    return medication_row(m)


@router.patch("/api/medications/{item_id}/toggle")
def toggle_medication(
    item_id: int,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    m = s.query(Medication).filter_by(id=item_id, user_id=user.id).first()
    if not m:
        raise HTTPException(404, "Medication not found")
    m.active = not bool(m.active)
    m.updated_at = datetime.utcnow()
    s.commit()
    s.refresh(m)
    return medication_row(m)


@router.delete("/api/medications/{item_id}")
def delete_medication(
    item_id: int,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    m = s.query(Medication).filter_by(id=item_id, user_id=user.id).first()
    if not m:
        raise HTTPException(404, "Medication not found")
    s.delete(m)
    s.commit()
    log_action(s, user.id, f"medication_deleted:{item_id}")
    return {"status": "deleted", "id": item_id}


# ══════════════════════════════════════════════════════════════════════
# Health metrics (vitals)
# ══════════════════════════════════════════════════════════════════════
def metric_row(m: HealthMetric) -> dict:
    return {
        "id": m.id,
        "metric": m.metric,
        "value": m.value,
        "unit": m.unit or "",
        "recorded_at": m.recorded_at,
        "notes": getattr(m, "notes", "") or "",
        "source": getattr(m, "source", "manual") or "manual",
    }


@router.get("/api/metrics")
def metrics(
    metric: str | None = None,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    query = s.query(HealthMetric).filter_by(user_id=user.id)
    if metric:
        query = query.filter(HealthMetric.metric == metric)
    rows = query.order_by(HealthMetric.id.asc()).all()
    return [metric_row(m) for m in rows]


@router.post("/api/metrics")
def add_metric(
    body: schemas.MetricIn,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    m = HealthMetric(user_id=user.id, **body.model_dump())
    s.add(m)
    s.commit()
    s.refresh(m)
    return metric_row(m)


@router.delete("/api/metrics/{item_id}")
def delete_metric(
    item_id: int,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    m = s.query(HealthMetric).filter_by(id=item_id, user_id=user.id).first()
    if not m:
        raise HTTPException(404, "Metric not found")
    s.delete(m)
    s.commit()
    return {"status": "deleted", "id": item_id}
