import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app, db as get_db
from app.database.models import Base

def test_auth_and_patient_workflows():
    engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
    TestingSession=sessionmaker(bind=engine,autoflush=False,autocommit=False)
    Base.metadata.create_all(bind=engine)
    def override_db():
        session=TestingSession()
        try: yield session
        finally: session.close()
    app.dependency_overrides[get_db]=override_db
    try:
        with TestClient(app) as client:
            r=client.post("/api/auth/register",json={"email":"api-test@example.com","name":"API Test","password":"StrongPass123"})
            assert r.status_code==200
            token=r.json()["access_token"]
            headers={"Authorization":f"Bearer {token}"}
            assert client.get("/api/auth/me",headers=headers).status_code==200
            appt=client.post("/api/appointments",headers=headers,json={"doctor_name":"Dr Demo","specialty":"General","appointment_at":"2026-11-20T10:00","notes":"test"})
            assert appt.status_code==200
            assert len(client.get("/api/appointments",headers=headers).json())==1
            assert client.get("/api/analytics/summary",headers=headers).json()["appointments"]==1
            assert client.post("/api/assistant",headers=headers,json={"message":"What is haemoglobin?"}).status_code==200
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
