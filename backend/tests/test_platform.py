"""End-to-end API tests for the extended MediSense platform.

Each test group runs against an isolated in-memory SQLite database by overriding
the ``db`` dependency exported from ``app.main``. Nothing is written to the
developer's on-disk database and no external AI provider is contacted.
"""
from __future__ import annotations

import io
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.models import Base, User
from app.main import app, db as get_db


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _register(client, email: str, name: str = "Test User", password: str = "StrongPass123"):
    response = client.post(
        "/api/auth/register", json={"email": email, "name": name, "password": password}
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    return {"Authorization": f"Bearer {payload['access_token']}"}, payload


def _make_admin(client, email: str):
    """Promote an account to admin directly in the DB (no self-service escalation)."""
    headers, payload = _register(client, email, "Admin User")
    session = next(app.dependency_overrides[get_db]())
    user = session.get(User, payload["user"]["id"])
    user.role = "admin"
    session.commit()
    session.close()
    # Re-login so the JWT carries the admin role.
    login = client.post(
        "/api/auth/login", json={"email": email, "password": "StrongPass123"}
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


# ══════════════════════════════════════════════════════════════════════
# Auth & profile
# ══════════════════════════════════════════════════════════════════════
def test_registration_returns_full_profile_and_settings(client):
    headers, payload = _register(client, "profile@example.com", "Ada Lovelace")
    assert payload["role"] == "patient"
    assert payload["user"]["email"] == "profile@example.com"
    assert payload["user"]["name"] == "Ada Lovelace"

    me = client.get("/api/auth/me", headers=headers).json()
    assert me["blood_group"] == ""
    assert me["is_verified"] is False

    settings = client.get("/api/settings", headers=headers)
    assert settings.status_code == 200
    assert settings.json()["theme"] == "system"


def test_duplicate_email_is_rejected(client):
    _register(client, "dup@example.com")
    second = client.post(
        "/api/auth/register",
        json={"email": "dup@example.com", "name": "Other", "password": "StrongPass123"},
    )
    assert second.status_code == 409


def test_weak_password_is_rejected(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "weak@example.com", "name": "Weak", "password": "passwordonly"},
    )
    assert response.status_code == 422


def test_profile_update_and_password_change(client):
    headers, _ = _register(client, "update@example.com")

    updated = client.put(
        "/api/auth/me",
        headers=headers,
        json={"blood_group": "O+", "phone": "+15550100", "gender": "female"},
    )
    assert updated.status_code == 200
    assert updated.json()["blood_group"] == "O+"

    changed = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={"current_password": "StrongPass123", "new_password": "NewStrongPass456"},
    )
    assert changed.status_code == 200

    relogin = client.post(
        "/api/auth/login",
        json={"email": "update@example.com", "password": "NewStrongPass456"},
    )
    assert relogin.status_code == 200

    wrong = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={"current_password": "totally-wrong", "new_password": "AnotherPass789"},
    )
    assert wrong.status_code == 401


def test_unauthenticated_access_is_blocked(client):
    for path in (
        "/api/auth/me",
        "/api/reports",
        "/api/appointments",
        "/api/medications",
        "/api/metrics",
        "/api/notifications",
        "/api/settings",
        "/api/health-records",
        "/api/support/tickets",
        "/api/wearables",
        "/api/analytics/summary",
        "/api/admin/stats",
    ):
        assert client.get(path).status_code == 401, path


# ══════════════════════════════════════════════════════════════════════
# Per-user isolation
# ══════════════════════════════════════════════════════════════════════
def test_records_are_isolated_between_patients(client):
    alice, _ = _register(client, "alice@example.com", "Alice")
    bob, _ = _register(client, "bob@example.com", "Bob")

    created = client.post(
        "/api/health-records",
        headers=alice,
        json={"title": "Blood panel", "record_type": "lab", "description": "private"},
    )
    assert created.status_code == 200
    record_id = created.json()["id"]

    assert len(client.get("/api/health-records", headers=alice).json()) == 1
    assert client.get("/api/health-records", headers=bob).json() == []

    # Bob must not be able to delete Alice's record.
    assert client.delete(f"/api/health-records/{record_id}", headers=bob).status_code == 404
    assert client.delete(f"/api/health-records/{record_id}", headers=alice).status_code == 200


def test_appointment_and_medication_lifecycle(client):
    headers, _ = _register(client, "lifecycle@example.com")

    appointment = client.post(
        "/api/appointments",
        headers=headers,
        json={
            "doctor_name": "Dr. Aarav Mehta",
            "specialty": "Cardiology",
            "appointment_at": "2026-12-01T09:30",
            "notes": "follow-up",
        },
    )
    assert appointment.status_code == 200
    appointment_id = appointment.json()["id"]

    cancelled = client.patch(f"/api/appointments/{appointment_id}/cancel", headers=headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    med = client.post(
        "/api/medications",
        headers=headers,
        json={"name": "Metformin", "dosage": "500 mg", "frequency": "twice daily"},
    )
    assert med.status_code == 200
    med_id = med.json()["id"]

    toggled = client.patch(f"/api/medications/{med_id}/toggle", headers=headers)
    assert toggled.status_code == 200
    assert toggled.json()["active"] is False

    metric = client.post(
        "/api/metrics",
        headers=headers,
        json={
            "metric": "Blood Pressure",
            "value": 128,
            "unit": "mmHg",
            "recorded_at": "2026-11-01T08:00",
        },
    )
    assert metric.status_code == 200

    summary = client.get("/api/analytics/summary", headers=headers).json()
    assert summary["appointments"] == 1
    assert summary["active_medications"] == 0  # toggled off above
    assert summary["metrics"] == 1
    assert summary["data_source"] == "database"


# ══════════════════════════════════════════════════════════════════════
# Report analysis (text extraction path, no OCR needed)
# ══════════════════════════════════════════════════════════════════════
def _text_report_upload(text: str):
    # A minimal valid PDF is not required for the .txt path used by the analyser
    # tests; the endpoint also accepts plain text uploads for convenience.
    return {"file": ("report.txt", io.BytesIO(text.encode()), "text/plain")}


def test_report_analyze_accepts_text_and_flags_values(client):
    headers, _ = _register(client, "reports@example.com")
    status = client.get("/api/reports/ocr-status")
    assert status.status_code == 200
    assert "available" in status.json()

    response = client.post(
        "/api/reports/analyze",
        headers=headers,
        files=_text_report_upload("Haemoglobin 11.2 g/dL (13.0 - 17.0)\nVitamin D 18 ng/mL\n"),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    states = {p["name"]: p["status"] for p in body["parameters"]}
    assert states["Haemoglobin"] == "below_range"
    assert states["Vitamin D"] == "no_reference_range"
    assert body["counts"]["flagged"] >= 1
    assert body["disclaimer"]


def test_report_compare_returns_deltas(client):
    headers, _ = _register(client, "compare@example.com")
    first = client.post(
        "/api/reports/analyze",
        headers=headers,
        files=_text_report_upload("Glucose 100 mg/dL (70 - 100)\n"),
    ).json()
    second = client.post(
        "/api/reports/analyze",
        headers=headers,
        files=_text_report_upload("Glucose 90 mg/dL (70 - 100)\n"),
    ).json()

    compared = client.post(
        "/api/reports/compare",
        headers=headers,
        json={"report_ids": [first["id"], second["id"]]},
    )
    assert compared.status_code == 200, compared.text
    payload = compared.json()
    # The endpoint reports which report is chronologically older/newer.
    assert payload["older"]["id"] == first["id"]
    assert payload["newer"]["id"] == second["id"]
    glucose = [p for p in payload["rows"] if p["name"] == "Glucose"][0]
    assert glucose["previous"] == 100
    assert glucose["current"] == 90
    assert glucose["change"] == -10
    assert glucose["direction"] == "down"
    assert payload["compared"] == 1


def test_report_delete_enforces_ownership(client):
    alice, _ = _register(client, "owner@example.com")
    bob, _ = _register(client, "intruder@example.com")
    report = client.post(
        "/api/reports/analyze",
        headers=alice,
        files=_text_report_upload("Glucose 90 mg/dL (70 - 100)\n"),
    ).json()

    assert client.delete(f"/api/reports/{report['id']}", headers=bob).status_code == 404
    assert client.delete(f"/api/reports/{report['id']}", headers=alice).status_code == 200
    assert client.get(f"/api/reports/{report['id']}", headers=alice).status_code == 404


# ══════════════════════════════════════════════════════════════════════
# Assistant + notifications + support
# ══════════════════════════════════════════════════════════════════════
def test_assistant_persists_conversation_history(client):
    headers, _ = _register(client, "chat@example.com")

    availability = client.get("/api/assistant/availability").json()
    assert availability["mode"] in {"demo", "gemini", "openai"}

    conversation = client.post(
        "/api/assistant/conversations", headers=headers, json={"title": "Lab results"}
    )
    assert conversation.status_code == 200
    conversation_id = conversation.json()["id"]

    answer = client.post(
        "/api/assistant",
        headers=headers,
        json={"message": "Explain haemoglobin", "conversation_id": conversation_id},
    )
    assert answer.status_code == 200
    assert answer.json()["answer"].strip()
    # Demo mode must always be labelled, never presented as a live model call.
    assert answer.json()["mode"] in {"demo", "gemini", "openai"}

    detail = client.get(f"/api/assistant/conversations/{conversation_id}", headers=headers)
    assert detail.status_code == 200
    roles = [m["role"] for m in detail.json()["messages"]]
    assert roles == ["user", "assistant"]

    listing = client.get("/api/assistant/conversations", headers=headers).json()
    assert len(listing) == 1


def test_notifications_and_mark_read(client):
    headers, _ = _register(client, "notify@example.com")
    created = client.post(
        "/api/notifications",
        headers=headers,
        json={"title": "Appointment reminder", "message": "Tomorrow 9am", "type": "reminder"},
    )
    assert created.status_code == 200
    notification_id = created.json()["id"]

    unread = client.get("/api/notifications?unread_only=true", headers=headers).json()
    assert len(unread) == 1

    assert (
        client.patch(f"/api/notifications/{notification_id}/read", headers=headers).json()[
            "is_read"
        ]
        is True
    )
    assert client.get("/api/notifications?unread_only=true", headers=headers).json() == []


def test_support_ticket_flow(client):
    headers, _ = _register(client, "support@example.com")
    faq = client.get("/api/support/faq")
    assert faq.status_code == 200
    assert faq.json() and {"question", "answer"} <= set(faq.json()[0])

    ticket = client.post(
        "/api/support/tickets",
        headers=headers,
        json={
            "subject": "Cannot upload a scan",
            "description": "Upload fails on a scanned PDF.",
            "category": "technical",
            "priority": "high",
        },
    )
    assert ticket.status_code == 200
    ticket_id = ticket.json()["id"]

    replied = client.post(
        f"/api/support/tickets/{ticket_id}/messages",
        headers=headers,
        json={"message": "Any update?"},
    )
    assert replied.status_code == 200

    detail = client.get(f"/api/support/tickets/{ticket_id}", headers=headers).json()
    assert len(detail["messages"]) >= 2


# ══════════════════════════════════════════════════════════════════════
# Doctors, wearables, analytics, admin
# ══════════════════════════════════════════════════════════════════════
def test_doctor_directory_is_public_and_searchable(client, monkeypatch):
    from app.database.models import Doctor

    session = next(app.dependency_overrides[get_db]())
    session.add(
        Doctor(
            name="Dr. Test Cardiology",
            specialty="Cardiology",
            hospital="Test Hospital",
            rating=4.9,
            is_active=True,
            is_demo=True,
        )
    )
    session.commit()
    session.close()

    listing = client.get("/api/doctors")
    assert listing.status_code == 200
    body = listing.json()
    assert body["count"] == 1
    assert body["doctors"][0]["is_demo"] is True

    filtered = client.get("/api/doctors?search=cardio").json()
    assert filtered["count"] == 1
    assert client.get("/api/doctors?specialty=Neurology").json()["count"] == 0


def test_wearables_architecture_and_registration(client):
    headers, _ = _register(client, "wearable@example.com")
    architecture = client.get("/api/wearables/architecture").json()
    # Vendor sync stays explicitly "not configured" until OAuth credentials exist.
    assert architecture["vendors"]
    assert all(v["status"] != "connected" for v in architecture["vendors"])
    assert architecture["ingest_endpoint"] == "/api/wearables/{device_id}/sync"

    device_type = architecture["supported_devices"][0]["type"]
    device = client.post(
        "/api/wearables",
        headers=headers,
        json={"device_type": device_type, "device_name": "Test Watch"},
    )
    assert device.status_code == 200
    # A newly registered device must not claim to be connected to a real vendor.
    assert device.json()["connection_status"] != "connected"
    assert len(client.get("/api/wearables", headers=headers).json()) == 1
    reading = client.post(
        f"/api/wearables/{device.json()['id']}/sync",
        headers=headers,
        json={"samples": [{"metric": "heart_rate", "value": 72, "unit": "bpm", "recorded_at": "2026-11-03T10:00:00"}]},
    )
    assert reading.status_code == 200
    assert reading.json()["stored"] == 1
    assert reading.json()["device"]["connection_status"] == "connected"

    rejected = client.post(
        "/api/wearables", headers=headers, json={"device_type": "not-a-real-device"}
    )
    assert rejected.status_code == 422


def test_analytics_timeline_and_health_summary(client):
    headers, _ = _register(client, "analytics@example.com")
    client.post(
        "/api/metrics",
        headers=headers,
        json={
            "metric": "Weight",
            "value": 72.5,
            "unit": "kg",
            "recorded_at": "2026-10-01T07:00",
        },
    )
    client.post(
        "/api/metrics",
        headers=headers,
        json={
            "metric": "Weight",
            "value": 71.0,
            "unit": "kg",
            "recorded_at": "2026-10-08T07:00",
        },
    )

    summary = client.get("/api/analytics/health-summary", headers=headers).json()
    weight = [m for m in summary["metrics"] if m["metric"] == "Weight"][0]
    assert weight["latest"] == 71.0
    assert weight["delta"] == -1.5
    assert weight["direction"] == "down"
    assert len(weight["series"]) == 2

    client.post(
        "/api/health-records",
        headers=headers,
        json={"title": "Annual physical", "record_type": "note"},
    )
    timeline = client.get("/api/analytics/timeline", headers=headers).json()
    assert any(event["type"] == "record" for event in timeline)
    assert {e["type"] for e in timeline} == {"record"}


def test_admin_endpoints_require_admin_role(client):
    patient, _ = _register(client, "notadmin@example.com")
    for path in ("/api/admin/stats", "/api/admin/users", "/api/admin/audit"):
        assert client.get(path, headers=patient).status_code == 403, path

    admin = _make_admin(client, "admin@example.com")
    stats = client.get("/api/admin/stats", headers=admin)
    assert stats.status_code == 200
    assert stats.json()["users"] >= 2

    users = client.get("/api/admin/users", headers=admin).json()
    assert len(users) >= 2
    assert "password_hash" not in json.dumps(users)

    created = client.post(
        "/api/admin/doctors",
        headers=admin,
        json={"name": "Dr. Added By Admin", "specialty": "Neurology"},
    )
    assert created.status_code == 200
    assert created.json()["is_demo"] is False

    role_change = client.patch(
        f"/api/admin/users/{users[0]['id']}/role", headers=admin, json={"role": "doctor"}
    )
    assert role_change.status_code in (200, 422)


def test_doctor_workspace_requires_doctor_role(client):
    patient, _ = _register(client, "patient-doc@example.com")
    assert client.get("/api/doctor/stats", headers=patient).status_code == 403

    doctor_headers, _ = _register(client, "doctor@example.com", "Dr. Real")
    session = next(app.dependency_overrides[get_db]())
    doctor_user = session.query(User).filter_by(email="doctor@example.com").first()
    doctor_user.role = "doctor"
    session.commit()
    session.close()

    login = client.post(
        "/api/auth/login",
        json={"email": "doctor@example.com", "password": "StrongPass123"},
    )
    doctor_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    stats = client.get("/api/doctor/stats", headers=doctor_headers)
    assert stats.status_code == 200
    assert stats.json()["total_appointments"] == 0
    assert client.get("/api/doctor/profile", headers=doctor_headers).status_code == 200


def test_voice_config_is_secret_free_and_ask_returns_speech(client):
    config = client.get("/api/voice/config").json()
    assert config["server_tts"] is False
    assert config["privacy"] == "no_audio_upload"

    headers, _ = _register(client, "voice@example.com")
    answer = client.post(
        "/api/voice/ask", headers=headers, json={"message": "What is blood pressure?"}
    )
    assert answer.status_code == 200
    body = answer.json()
    assert body["speech"]["text"]
    assert "**" not in body["speech"]["text"]


def test_meta_endpoint_never_leaks_secrets(client):
    import os

    meta = client.get("/api/meta")
    assert meta.status_code == 200
    body = meta.json()
    assert body["app"] == "MediSense"
    assert set(body["features"]) >= {"pwa", "voice", "anatomy3d"}

    serialised = json.dumps(body)
    # No configured credential value may ever appear in public metadata.
    for name in ("SECRET_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY"):
        value = os.getenv(name)
        if value and len(value) >= 8:
            assert value not in serialised, f"{name} value leaked via /api/meta"
    lowered = serialised.lower()
    assert "bearer " not in lowered
    assert "password_hash" not in lowered
