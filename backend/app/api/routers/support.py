"""Support centre and wearable device architecture."""
from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import schemas
from app.api.deps import current_user, db, log_action, notify, require
from app.database.models import (
    HealthMetric,
    SupportMessage,
    SupportTicket,
    User,
    WearableDevice,
)

router = APIRouter(tags=["support"])


# ══════════════════════════════════════════════════════════════════════
# Support tickets
# ══════════════════════════════════════════════════════════════════════
def ticket_row(t: SupportTicket, with_messages: bool = False) -> dict:
    payload = {
        "id": t.id,
        "subject": t.subject,
        "description": t.description or "",
        "category": t.category or "general",
        "status": t.status or "open",
        "priority": t.priority or "medium",
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }
    if with_messages:
        payload["messages"] = [
            {
                "id": m.id,
                "message": m.message,
                "is_staff": bool(m.is_staff),
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in t.ticket_messages
        ]
    return payload


def _ticket(s: Session, ticket_id: int, user: User) -> SupportTicket:
    query = s.query(SupportTicket).filter_by(id=ticket_id)
    if user.role != "admin":
        query = query.filter(SupportTicket.user_id == user.id)
    ticket = query.first()
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    return ticket


@router.get("/api/support/tickets")
def list_tickets(user: User = Depends(current_user), s: Session = Depends(db)):
    query = s.query(SupportTicket)
    if user.role != "admin":
        query = query.filter(SupportTicket.user_id == user.id)
    rows = query.order_by(SupportTicket.updated_at.desc(), SupportTicket.id.desc()).all()
    return [ticket_row(t) for t in rows]


@router.post("/api/support/tickets")
def create_ticket(
    body: schemas.TicketIn,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    ticket = SupportTicket(user_id=user.id, **body.model_dump())
    s.add(ticket)
    s.flush()  # assign ticket.id before creating the first message
    # The opening description is the first message so the thread keeps the
    # original problem statement alongside later replies.
    if (ticket.description or "").strip():
        s.add(
            SupportMessage(
                ticket_id=ticket.id,
                user_id=user.id,
                message=ticket.description.strip(),
                is_staff=False,
            )
        )
    s.commit()
    s.refresh(ticket)
    log_action(s, user.id, f"ticket_created:{ticket.id}")
    return ticket_row(ticket, with_messages=True)


@router.get("/api/support/tickets/{ticket_id}")
def get_ticket(
    ticket_id: int,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    return ticket_row(_ticket(s, ticket_id, user), with_messages=True)


@router.post("/api/support/tickets/{ticket_id}/messages")
def add_message(
    ticket_id: int,
    body: schemas.TicketMessageIn,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    ticket = _ticket(s, ticket_id, user)
    is_staff = user.role == "admin"
    s.add(
        SupportMessage(
            ticket_id=ticket.id,
            user_id=user.id,
            message=body.message,
            is_staff=is_staff,
        )
    )
    ticket.updated_at = datetime.utcnow()
    if is_staff and ticket.status == "open":
        ticket.status = "in_progress"
    s.commit()
    if not is_staff:
        notify(
            s,
            ticket.user_id,
            "Support reply saved",
            "Your message was added to the ticket.",
            type="info",
        )
    return ticket_row(_ticket(s, ticket_id, user), with_messages=True)


@router.patch("/api/support/tickets/{ticket_id}/status")
def set_status(
    ticket_id: int,
    body: schemas.TicketStatusIn,
    user: User = Depends(require("admin")),
    s: Session = Depends(db),
):
    ticket = _ticket(s, ticket_id, user)
    ticket.status = body.status
    ticket.updated_at = datetime.utcnow()
    s.commit()
    notify(
        s,
        ticket.user_id,
        f"Ticket {body.status.replace('_', ' ')}",
        ticket.subject,
        type="info",
    )
    log_action(s, user.id, f"ticket_status:{ticket_id}:{body.status}")
    return ticket_row(ticket)


@router.delete("/api/support/tickets/{ticket_id}")
def delete_ticket(
    ticket_id: int,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    ticket = _ticket(s, ticket_id, user)
    s.delete(ticket)
    s.commit()
    return {"status": "deleted", "id": ticket_id}


@router.get("/api/support/faq")
def faq():
    """Static help content served from the backend so the UI has one source."""
    return [
        {
            "question": "Is MediSense a substitute for a doctor?",
            "answer": "No. MediSense explains medical terms and organises your records. "
            "Diagnosis and treatment always require a qualified clinician.",
        },
        {
            "question": "How are reference ranges decided?",
            "answer": "MediSense only uses the reference range printed in the report you "
            "upload. If your report has no printed range, the value is shown as "
            "'no reference range' instead of being guessed.",
        },
        {
            "question": "Which AI provider answers the assistant?",
            "answer": "The platform administrator configures Gemini, OpenAI or the built-in "
            "demo mode. The active mode is always shown on the assistant screen.",
        },
        {
            "question": "Can I connect my smartwatch?",
            "answer": "The wearable framework is available. Vendor connections require an "
            "OAuth app from the manufacturer; until one is configured the app shows "
            "'not configured' rather than simulating a device.",
        },
        {
            "question": "Who can see my reports?",
            "answer": "Reports are scoped to your account. Every API call is filtered by "
            "your user id and recorded in the audit log.",
        },
    ]


# ══════════════════════════════════════════════════════════════════════
# Wearables
# ══════════════════════════════════════════════════════════════════════
SUPPORTED_DEVICES = [
    {"type": "smartwatch", "label": "Smartwatch"},
    {"type": "fitness_band", "label": "Fitness band"},
    {"type": "smart_ring", "label": "Smart ring"},
    {"type": "glucose_monitor", "label": "Glucose monitor"},
    {"type": "blood_pressure_cuff", "label": "Blood pressure cuff"},
]

# Vendors the platform can integrate with once OAuth credentials exist.
VENDOR_INTEGRATIONS = [
    {"vendor": "Fitbit", "status": "not_configured", "requires": "FITBIT_CLIENT_ID / FITBIT_CLIENT_SECRET"},
    {"vendor": "Google Health Connect", "status": "not_configured", "requires": "GOOGLE_HEALTH_CLIENT_ID"},
    {"vendor": "Apple Health", "status": "requires_mobile_app", "requires": "Native iOS bridge"},
]

SYNC_FIELDS = {"metric", "value", "unit", "recorded_at", "notes"}


def device_row(d: WearableDevice) -> dict:
    return {
        "id": d.id,
        "device_type": d.device_type,
        "device_name": d.device_name or "",
        "connection_status": d.connection_status or "disconnected",
        "last_synced": d.last_synced.isoformat() if d.last_synced else None,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


@router.get("/api/wearables")
def list_wearables(user: User = Depends(current_user), s: Session = Depends(db)):
    rows = s.query(WearableDevice).filter_by(user_id=user.id).all()
    return [device_row(d) for d in rows]


@router.get("/api/wearables/architecture")
def wearable_architecture():
    """Explicit integration status — never implies a live vendor connection."""
    return {
        "supported_devices": SUPPORTED_DEVICES,
        "vendors": VENDOR_INTEGRATIONS,
        "ingest_endpoint": "/api/wearables/{device_id}/sync",
        "notes": "Devices are registered locally. Automatic vendor sync requires OAuth "
        "credentials configured server-side; manual ingestion via the sync endpoint is "
        "fully functional and stores real measurements.",
    }


@router.post("/api/wearables")
def register_wearable(
    body: schemas.WearableIn,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    known = {d["type"] for d in SUPPORTED_DEVICES}
    if body.device_type not in known:
        raise HTTPException(422, f"Unsupported device type. Choose one of: {sorted(known)}")
    device = WearableDevice(
        user_id=user.id,
        device_type=body.device_type,
        device_name=body.device_name or "",
        connection_status="registered",
        permissions_json=json.dumps({"scopes": ["metrics:write"]}),
    )
    s.add(device)
    s.commit()
    s.refresh(device)
    log_action(s, user.id, f"wearable_registered:{device.id}")
    return device_row(device)


@router.post("/api/wearables/{device_id}/sync")
def sync_wearable(
    device_id: int,
    body: schemas.WearableSyncIn,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    """Ingest real measurements for a registered device.

    The payload must contain actual samples; nothing is fabricated. Missing
    vendor credentials are not simulated — the samples come from the caller.
    """
    device = s.query(WearableDevice).filter_by(id=device_id, user_id=user.id).first()
    if not device:
        raise HTTPException(404, "Device not found")
    if not body.samples:
        raise HTTPException(422, "Provide at least one measurement sample")

    stored, rejected = 0, []
    for index, sample in enumerate(body.samples):
        if not isinstance(sample, dict):
            rejected.append({"index": index, "reason": "not an object"})
            continue
        metric = str(sample.get("metric", "")).strip()
        value = sample.get("value")
        recorded_at = str(sample.get("recorded_at", "")).strip()
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            rejected.append({"index": index, "reason": "value is not numeric"})
            continue
        if not metric or not recorded_at:
            rejected.append({"index": index, "reason": "metric and recorded_at are required"})
            continue
        s.add(
            HealthMetric(
                user_id=user.id,
                metric=metric[:80],
                value=numeric,
                unit=str(sample.get("unit", ""))[:30],
                recorded_at=recorded_at[:40],
                notes=str(sample.get("notes", ""))[:500],
                source="wearable",
            )
        )
        stored += 1

    if stored == 0:
        raise HTTPException(422, f"No valid samples. Rejected: {rejected[:5]}")

    device.last_synced = datetime.utcnow()
    device.connection_status = "connected"
    s.commit()
    log_action(s, user.id, f"wearable_sync:{device.id}:{stored}")
    return {"stored": stored, "rejected": rejected, "device": device_row(device)}


@router.delete("/api/wearables/{device_id}")
def remove_wearable(
    device_id: int,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    device = s.query(WearableDevice).filter_by(id=device_id, user_id=user.id).first()
    if not device:
        raise HTTPException(404, "Device not found")
    s.delete(device)
    s.commit()
    return {"status": "deleted", "id": device_id}
