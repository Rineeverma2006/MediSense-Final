"""Doctor directory.

Doctors are stored in the database. The rows created by the demo seeder are
explicitly flagged ``is_demo`` so the UI can label them as sample data rather
than presented as real practitioners.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api import schemas
from app.api.deps import current_user, db, log_action, require
from app.database.models import Appointment, Doctor, User

router = APIRouter(tags=["doctors"])

SPECIALTIES = [
    "General Physician",
    "Cardiology",
    "Dermatology",
    "Endocrinology",
    "Gastroenterology",
    "Neurology",
    "Orthopaedics",
    "Paediatrics",
    "Psychiatry",
    "Pulmonology",
    "Radiology",
    "Urology",
]


def doctor_row(d: Doctor) -> dict:
    return {
        "id": d.id,
        "name": d.name,
        "specialty": d.specialty,
        "qualification": d.qualification or "",
        "experience": d.experience or "",
        "hospital": d.hospital or "",
        "rating": d.rating or 0.0,
        "consultation_fee": d.consultation_fee or 0.0,
        "image": d.image_url or "",
        "image_url": d.image_url or "",
        "about": d.about or "",
        "email": d.email or "",
        "phone": d.phone or "",
        "is_active": bool(d.is_active),
        "is_demo": bool(getattr(d, "is_demo", False)),
    }


@router.get("/api/doctors")
def list_doctors(
    search: str | None = None,
    specialty: str | None = None,
    s: Session = Depends(db),
):
    """Public directory — no authentication needed, no patient data exposed."""
    query = s.query(Doctor).filter(Doctor.is_active.is_(True))
    if specialty:
        query = query.filter(Doctor.specialty == specialty)
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Doctor.name.ilike(like),
                Doctor.specialty.ilike(like),
                Doctor.hospital.ilike(like),
            )
        )
    rows = query.order_by(Doctor.rating.desc(), Doctor.name.asc()).all()
    return {
        "doctors": [doctor_row(d) for d in rows],
        "specialties": sorted({d.specialty for d in s.query(Doctor).all()}) or SPECIALTIES,
        "count": len(rows),
    }


@router.get("/api/doctors/{doctor_id}")
def get_doctor(doctor_id: int, s: Session = Depends(db)):
    doctor = s.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(404, "Doctor not found")
    return doctor_row(doctor)


# ══════════════════════════════════════════════════════════════════════
# Doctor workspace (role: doctor)
# ══════════════════════════════════════════════════════════════════════
@router.get("/api/doctor/profile")
def my_doctor_profile(
    user: User = Depends(require("doctor")), s: Session = Depends(db)
):
    doctor = s.query(Doctor).filter(Doctor.email == user.email).first()
    if not doctor:
        return {
            "linked": False,
            "detail": "No directory profile is linked to this account yet. "
            "An administrator can create one.",
            "name": user.name,
        }
    return {"linked": True, "doctor": doctor_row(doctor)}


@router.get("/api/doctor/appointments")
def doctor_appointments(
    user: User = Depends(require("doctor")), s: Session = Depends(db)
):
    doctor = s.query(Doctor).filter(Doctor.email == user.email).first()
    query = s.query(Appointment)
    if doctor:
        query = query.filter(
            or_(Appointment.doctor_id == doctor.id, Appointment.doctor_name == doctor.name)
        )
    else:
        # Fall back to name matching so a doctor still sees their own queue.
        query = query.filter(Appointment.doctor_name == user.name)
    rows = query.order_by(Appointment.appointment_at.desc()).all()
    return [
        {
            "id": a.id,
            "patient_id": a.user_id,
            "doctor_name": a.doctor_name,
            "specialty": a.specialty,
            "appointment_at": a.appointment_at,
            "status": a.status,
            "notes": a.notes or "",
        }
        for a in rows
    ]


@router.get("/api/doctor/stats")
def doctor_stats(user: User = Depends(require("doctor")), s: Session = Depends(db)):
    doctor = s.query(Doctor).filter(Doctor.email == user.email).first()
    query = s.query(Appointment)
    if doctor:
        query = query.filter(
            or_(Appointment.doctor_id == doctor.id, Appointment.doctor_name == doctor.name)
        )
    else:
        query = query.filter(Appointment.doctor_name == user.name)
    rows = query.all()
    statuses = {}
    for row in rows:
        statuses[row.status] = statuses.get(row.status, 0) + 1
    return {
        "total_appointments": len(rows),
        "upcoming": len([r for r in rows if r.status == "scheduled"]),
        "completed": len([r for r in rows if r.status == "completed"]),
        "cancelled": len([r for r in rows if r.status == "cancelled"]),
        "unique_patients": len({r.user_id for r in rows}),
        "by_status": statuses,
        "linked_profile": bool(doctor),
    }


# ══════════════════════════════════════════════════════════════════════
# Administrative directory management
# ══════════════════════════════════════════════════════════════════════
@router.get("/api/admin/doctors")
def admin_list_doctors(
    user: User = Depends(require("admin")), s: Session = Depends(db)
):
    rows = s.query(Doctor).order_by(Doctor.id.asc()).all()
    return [doctor_row(d) for d in rows]


@router.post("/api/admin/doctors")
def admin_create_doctor(
    body: schemas.DoctorIn,
    user: User = Depends(require("admin")),
    s: Session = Depends(db),
):
    if body.email and s.query(Doctor).filter(Doctor.email == body.email).first():
        raise HTTPException(409, "A doctor with this email already exists")
    doctor = Doctor(**body.model_dump(), is_demo=False)
    s.add(doctor)
    s.commit()
    s.refresh(doctor)
    log_action(s, user.id, f"doctor_created:{doctor.id}")
    return doctor_row(doctor)


@router.put("/api/admin/doctors/{doctor_id}")
def admin_update_doctor(
    doctor_id: int,
    body: schemas.DoctorIn,
    user: User = Depends(require("admin")),
    s: Session = Depends(db),
):
    doctor = s.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(404, "Doctor not found")
    for field, value in body.model_dump().items():
        setattr(doctor, field, value)
    doctor.is_demo = False
    s.commit()
    s.refresh(doctor)
    log_action(s, user.id, f"doctor_updated:{doctor_id}")
    return doctor_row(doctor)


@router.delete("/api/admin/doctors/{doctor_id}")
def admin_delete_doctor(
    doctor_id: int,
    user: User = Depends(require("admin")),
    s: Session = Depends(db),
):
    doctor = s.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(404, "Doctor not found")
    s.delete(doctor)
    s.commit()
    log_action(s, user.id, f"doctor_deleted:{doctor_id}")
    return {"status": "deleted", "id": doctor_id}
