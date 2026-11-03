from app.database.models import Base,engine,SessionLocal,User,Appointment,Medication,HealthMetric
from app.core.security import hash_password
Base.metadata.create_all(bind=engine)
s=SessionLocal()
try:
    user=s.query(User).filter_by(email="patient@medisense.demo").first()
    if not user:
        user=User(email="patient@medisense.demo",name="Shubham Raj",role="patient",password_hash=hash_password("MediSense@123"))
        s.add(user); s.commit(); s.refresh(user)
    elif user.name != "Shubham Raj":
        user.name="Shubham Raj"
        s.commit()
    admin=s.query(User).filter_by(email="admin@medisense.demo").first()
    if not admin:
        s.add(User(email="admin@medisense.demo",name="MediSense Admin",role="admin",password_hash=hash_password("AdminDemo@123")))
        s.commit()
    if not s.query(Appointment).filter_by(user_id=user.id).first():
        s.add_all([
          Appointment(user_id=user.id,doctor_name="Dr. Neha Verma",specialty="General Physician",appointment_at="2026-11-05 10:30",status="scheduled",notes="Demo appointment"),
          Appointment(user_id=user.id,doctor_name="Dr. Arjun Mehta",specialty="Cardiology",appointment_at="2026-11-12 11:30",status="scheduled",notes="Demo appointment")])
    if not s.query(Medication).filter_by(user_id=user.id).first():
        s.add(Medication(user_id=user.id,name="Sample medication (demo only)",dosage="As prescribed",frequency="Daily",active=True))
    if not s.query(HealthMetric).filter_by(user_id=user.id).first():
        for metric,value,unit,date in [("Blood pressure",118,"mmHg","2026-08-01"),("Heart rate",72,"bpm","2026-09-01"),("Weight",72.5,"kg","2026-10-01")]:
            s.add(HealthMetric(user_id=user.id,metric=metric,value=value,unit=unit,recorded_at=date))
    s.commit()
    print("Demo patient: patient@medisense.demo / MediSense@123")
    print("Demo admin: admin@medisense.demo / AdminDemo@123")
    print("All seeded records are synthetic demo data, not clinical records.")
finally: s.close()
