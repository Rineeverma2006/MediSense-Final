"""Request/response schemas for the MediSense API."""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

Role = Literal["patient", "doctor", "admin"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def _clean_email(value: str) -> str:
    email = (value or "").strip().lower()
    if not EMAIL_RE.match(email):
        raise ValueError("Enter a valid email address")
    return email


# ── Auth ──────────────────────────────────────────────────────────────
class RegisterIn(BaseModel):
    email: str
    name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    role: Role = "patient"

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _clean_email(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("Password must contain at least one letter and one digit")
        return v


class LoginIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _clean_email(v)


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class ProfileUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    phone: Optional[str] = Field(default=None, max_length=20)
    blood_group: Optional[str] = Field(default=None, max_length=10)
    date_of_birth: Optional[str] = Field(default=None, max_length=20)
    gender: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=500)
    emergency_contact: Optional[str] = Field(default=None, max_length=255)
    profile_image: Optional[str] = Field(default=None, max_length=500)


# ── Assistant ─────────────────────────────────────────────────────────
class AskIn(BaseModel):
    message: str = Field(min_length=2, max_length=2000)
    conversation_id: Optional[int] = None


class ConversationIn(BaseModel):
    title: str = Field(default="New Conversation", max_length=255)


# ── Appointments ──────────────────────────────────────────────────────
class AppointmentIn(BaseModel):
    doctor_name: str = Field(min_length=1, max_length=120)
    specialty: str = Field(min_length=1, max_length=100)
    appointment_at: str = Field(min_length=4, max_length=40)
    notes: str = ""
    doctor_id: Optional[int] = None


class AppointmentStatusIn(BaseModel):
    status: Literal["scheduled", "completed", "cancelled"]


# ── Medications ───────────────────────────────────────────────────────
class MedicationIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    dosage: str = ""
    frequency: str = ""
    start_date: str = ""
    end_date: str = ""


class MedicationUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    active: Optional[bool] = None


# ── Metrics / vitals ──────────────────────────────────────────────────
class MetricIn(BaseModel):
    metric: str = Field(min_length=1, max_length=80)
    value: float
    unit: str = ""
    recorded_at: str = Field(min_length=4, max_length=40)
    notes: str = ""
    source: str = "manual"


# ── Health records ────────────────────────────────────────────────────
class HealthRecordIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    record_type: str = Field(default="general", max_length=50)
    date: str = Field(default="", max_length=30)
    description: str = ""


# ── Notifications ─────────────────────────────────────────────────────
class NotificationIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    message: str = ""
    type: Literal["info", "warning", "success", "reminder"] = "info"
    user_id: Optional[int] = None


# ── Settings ──────────────────────────────────────────────────────────
class SettingsIn(BaseModel):
    theme: Optional[Literal["light", "dark", "system"]] = None
    language: Optional[str] = Field(default=None, max_length=10)
    notifications_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None


# ── Support ───────────────────────────────────────────────────────────
class TicketIn(BaseModel):
    subject: str = Field(min_length=3, max_length=255)
    description: str = Field(default="", max_length=4000)
    category: str = Field(default="general", max_length=50)
    priority: Literal["low", "medium", "high", "urgent"] = "medium"


class TicketStatusIn(BaseModel):
    status: Literal["open", "in_progress", "resolved", "closed"]


class TicketMessageIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


# ── Wearables ─────────────────────────────────────────────────────────
class WearableIn(BaseModel):
    device_type: str = Field(min_length=2, max_length=50)
    device_name: str = Field(default="", max_length=120)


class WearableSyncIn(BaseModel):
    """Sample payload accepted by the wearable ingestion endpoint.

    A real vendor integration (Fitbit/Google Health/Apple Health) must call this
    endpoint server-side after OAuth; the browser never holds provider tokens.
    """

    samples: list[dict[str, Any]] = Field(default_factory=list, max_length=500)


# ── Reports ───────────────────────────────────────────────────────────
class ReportCompareIn(BaseModel):
    report_ids: list[int] = Field(min_length=2, max_length=2)


# ── Doctors / admin ───────────────────────────────────────────────────
class DoctorIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    specialty: str = Field(min_length=1, max_length=100)
    qualification: str = ""
    experience: str = ""
    hospital: str = ""
    rating: float = 0.0
    consultation_fee: float = 0.0
    image_url: str = ""
    about: str = ""
    email: str = ""
    phone: str = ""
    is_active: bool = True


class RoleIn(BaseModel):
    role: Role


class DoctorDecisionIn(BaseModel):
    decision: Literal["approve", "reject", "complete"]
    note: str = Field(default="", max_length=1000)


class FamilyMemberIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    relationship_type: str = Field(default="", max_length=50)
    date_of_birth: str = ""
    blood_group: str = ""
    notes: str = ""


# ── Voice assistant ───────────────────────────────────────────────────
class SpeakIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


__all__ = [
    "Role",
    "RegisterIn",
    "LoginIn",
    "ChangePasswordIn",
    "ProfileUpdateIn",
    "AskIn",
    "ConversationIn",
    "AppointmentIn",
    "AppointmentStatusIn",
    "MedicationIn",
    "MedicationUpdateIn",
    "MetricIn",
    "HealthRecordIn",
    "NotificationIn",
    "SettingsIn",
    "TicketIn",
    "TicketStatusIn",
    "TicketMessageIn",
    "WearableIn",
    "WearableSyncIn",
    "ReportCompareIn",
    "DoctorIn",
    "RoleIn",
    "DoctorDecisionIn",
    "FamilyMemberIn",
    "SpeakIn",
    "EmailStr",
    "date",
    "datetime",
]
