"""
MediSense – SQLAlchemy ORM models.

Every model that belongs to a user has a foreign-key to `users.id`.
Relationships are defined so you can navigate e.g. user.reports, user.appointments, etc.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey,
)
from sqlalchemy.orm import relationship
from app.database import Base, engine, SessionLocal  # re-export for compatibility


# ═══════════════════════════════════════════════════════════════════════
# User
# ═══════════════════════════════════════════════════════════════════════
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    role = Column(String(20), default="patient", nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), default="")
    profile_image = Column(String(500), default="")
    blood_group = Column(String(10), default="")
    date_of_birth = Column(String(20), default="")
    gender = Column(String(20), default="")
    address = Column(Text, default="")
    emergency_contact = Column(String(255), default="")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    reports = relationship("Report", back_populates="user", lazy="dynamic")
    appointments = relationship("Appointment", back_populates="user", lazy="dynamic")
    medications = relationship("Medication", back_populates="user", lazy="dynamic")
    metrics = relationship("HealthMetric", back_populates="user", lazy="dynamic")
    conversations = relationship("Conversation", back_populates="user", lazy="dynamic")
    health_records = relationship("HealthRecord", back_populates="user", lazy="dynamic")
    vital_records = relationship("VitalRecord", back_populates="user", lazy="dynamic")
    notifications = relationship("Notification", back_populates="user", lazy="dynamic")
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    support_tickets = relationship("SupportTicket", back_populates="user", lazy="dynamic")
    wearable_devices = relationship("WearableDevice", back_populates="user", lazy="dynamic")
    family_members = relationship("FamilyMember", back_populates="user", lazy="dynamic")


# ═══════════════════════════════════════════════════════════════════════
# Reports
# ═══════════════════════════════════════════════════════════════════════
class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    analysis_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="reports")


# ═══════════════════════════════════════════════════════════════════════
# Appointments
# ═══════════════════════════════════════════════════════════════════════
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True, index=True)
    doctor_name = Column(String(120), nullable=False)
    specialty = Column(String(100), nullable=False)
    appointment_at = Column(String(40), nullable=False)
    status = Column(String(30), default="scheduled")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="appointments")


# ═══════════════════════════════════════════════════════════════════════
# Medications
# ═══════════════════════════════════════════════════════════════════════
class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String(120), nullable=False)
    dosage = Column(String(100), default="")
    frequency = Column(String(100), default="")
    start_date = Column(String(30), default="")
    end_date = Column(String(30), default="")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="medications")


# ═══════════════════════════════════════════════════════════════════════
# Health Metrics (legacy, kept for backward-compat with /api/metrics)
# ═══════════════════════════════════════════════════════════════════════
class HealthMetric(Base):
    __tablename__ = "health_metrics"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    metric = Column(String(80), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(30), default="")
    recorded_at = Column(String(40), nullable=False)
    notes = Column(Text, default="")
    source = Column(String(50), default="manual")  # manual | wearable | import
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="metrics")


# ═══════════════════════════════════════════════════════════════════════
# Audit Log
# ═══════════════════════════════════════════════════════════════════════
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String(160), nullable=False)
    at = Column(DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════════════
# Doctor
# ═══════════════════════════════════════════════════════════════════════
class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    specialty = Column(String(100), nullable=False)
    qualification = Column(String(255), default="")
    experience = Column(String(50), default="")
    hospital = Column(String(200), default="")
    rating = Column(Float, default=0.0)
    consultation_fee = Column(Float, default=0.0)
    availability_json = Column(Text, default="{}")
    image_url = Column(String(500), default="")
    about = Column(Text, default="")
    email = Column(String(255), default="")
    phone = Column(String(20), default="")
    is_active = Column(Boolean, default=True)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════════════
# Conversations & Messages (AI assistant chat history)
# ═══════════════════════════════════════════════════════════════════════
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String(255), default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True, nullable=False)
    role = Column(String(20), nullable=False)   # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


# ═══════════════════════════════════════════════════════════════════════
# Health Records
# ═══════════════════════════════════════════════════════════════════════
class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    record_type = Column(String(50), default="general")  # e.g. lab, prescription, imaging
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    date = Column(String(30), default="")
    file_path = Column(String(500), default="")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="health_records")


# ═══════════════════════════════════════════════════════════════════════
# Vital Records
# ═══════════════════════════════════════════════════════════════════════
class VitalRecord(Base):
    __tablename__ = "vital_records"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    vital_type = Column(String(50), nullable=False)  # blood_pressure, heart_rate, weight …
    value = Column(Float, nullable=False)
    unit = Column(String(30), default="")
    recorded_at = Column(String(40), nullable=False)
    notes = Column(Text, default="")
    source = Column(String(50), default="manual")  # manual | wearable
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="vital_records")


# ═══════════════════════════════════════════════════════════════════════
# Notifications
# ═══════════════════════════════════════════════════════════════════════
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, default="")
    type = Column(String(30), default="info")  # info | warning | success | reminder
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


# ═══════════════════════════════════════════════════════════════════════
# User Settings
# ═══════════════════════════════════════════════════════════════════════
class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    theme = Column(String(20), default="system")
    language = Column(String(10), default="en")
    notifications_enabled = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="settings")


# ═══════════════════════════════════════════════════════════════════════
# Support Tickets & Messages
# ═══════════════════════════════════════════════════════════════════════
class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    subject = Column(String(255), nullable=False)
    description = Column(Text, default="")
    category = Column(String(50), default="general")
    status = Column(String(30), default="open")      # open | in_progress | resolved | closed
    priority = Column(String(20), default="medium")   # low | medium | high | urgent
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="support_tickets")
    ticket_messages = relationship(
        "SupportMessage", back_populates="ticket", cascade="all, delete-orphan",
        order_by="SupportMessage.created_at",
    )


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), index=True, nullable=False)
    user_id = Column(Integer, nullable=True)
    message = Column(Text, nullable=False)
    is_staff = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("SupportTicket", back_populates="ticket_messages")


# ═══════════════════════════════════════════════════════════════════════
# Wearable Devices
# ═══════════════════════════════════════════════════════════════════════
class WearableDevice(Base):
    __tablename__ = "wearable_devices"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    device_type = Column(String(50), nullable=False)  # smartwatch | fitness_band | …
    device_name = Column(String(120), default="")
    connection_status = Column(String(30), default="disconnected")
    last_synced = Column(DateTime, nullable=True)
    permissions_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="wearable_devices")


# ═══════════════════════════════════════════════════════════════════════
# Family Members
# ═══════════════════════════════════════════════════════════════════════
class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String(120), nullable=False)
    relationship_type = Column(String(50), default="")   # 'relationship' is a Python keyword on ORM
    date_of_birth = Column(String(20), default="")
    blood_group = Column(String(10), default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="family_members")
