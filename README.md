# MediSense — AI Healthcare Intelligence Platform

MediSense is an educational full-stack healthcare product prototype for a B.Tech CSE portfolio, college mini-project and hackathon demonstration. It combines a React/TypeScript dashboard with a Python FastAPI backend and SQLite database.

> **Clinical safety:** This is not a medical device and does not diagnose, prescribe or replace a clinician. Report analysis only compares extracted values against ranges explicitly printed in the uploaded report. Dashboard charts and seeded records are synthetic demo data.

## Included modules

- Patient login with JWT and salted PBKDF2 password hashing
- Dashboard with KPI cards, responsive charts and navigation
- AI assistant in clearly labelled demo mode
- PDF report text extraction and printed-range comparison
- Patient-owned report history
- Appointment booking and cancellation
- Medication list management
- Health metric recording and analytics summary
- Doctor directory with clearly labelled demo profiles
- Audit log endpoint for admin role
- Light/dark theme, responsive layout, Framer Motion transitions

## Requirements

- Windows 10/11
- Python 3.10–3.12 recommended
- Node.js 20 LTS or newer
- npm

## Quick start (Windows)

1. Extract the ZIP.
2. Open the extracted `MediSense_Final` folder.
3. Run `setup.bat`.
4. Run `start-all.bat`, or use `start-backend.bat` and `start-frontend.bat` in separate terminals.
6. Open http://localhost:5173

The setup script creates a Python virtual environment, installs backend requirements, creates `.env` from `.env.example` if missing, and installs frontend dependencies with `npm ci`.

### Demo login

- Email: `patient@medisense.demo`
- Password: `MediSense@123`\n- Admin API demo: `admin@medisense.demo` / `AdminDemo@123` (audit endpoint only; no full admin UI)

Demo user is created by `backend/seed_demo.py`. Run it once after setup if the login does not exist.

## Manual startup

Backend:
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python seed_demo.py
uvicorn app.main:app --reload --port 8000
```

Frontend (new terminal):
```powershell
cd frontend
npm install
npm run dev
```

API docs: http://localhost:8000/docs  
Health check: http://localhost:8000/api/health

## Configuration

Edit `backend/.env`:
- `SECRET_KEY`: replace with a long random secret before any shared deployment.
- `DATABASE_URL`: defaults to local SQLite. PostgreSQL URL is supported by SQLAlchemy.
- `AI_PROVIDER`: defaults to `demo`. The current assistant is deterministic demo content, not a live LLM.
- `CORS_ORIGINS`: comma-separated trusted frontend origins.

No API keys are included. Never place provider secrets in frontend environment variables.

## Current implementation boundaries

- Report extraction currently handles text-based PDFs and a limited set of common line-oriented result formats. Scanned PDFs need OCR integration; complex table layouts may need parser improvements.
- The demo assistant does not call a live AI provider.
- Doctor profiles and dashboard sample chart series are illustrative, not real provider availability or patient readings.
- Registration API is implemented; a dedicated sign-up screen is a future UI enhancement.
- Admin audit API is protected by role checks; a full admin console is not included yet.
- This prototype is not production-ready for real patient data. A production release needs a security/privacy review, encryption and retention policies, consent workflows, threat modelling, clinical validation, monitoring and applicable legal compliance.

## PWA and Android

The frontend build generates an installable PWA manifest and service worker. The service worker caches the static app shell only; it does not cache authenticated API responses. For Android, a Capacitor scaffold is in `frontend/android`; see `ANDROID_BUILD_GUIDE.md`. No APK is included because Android SDK/JDK builds have not been run in this environment.

## Project audit and build status

See `TECHNICAL_AUDIT.md`, `DEVELOPMENT_PROGRESS.md`, and `PROJECT_COMPLETION_STATUS.md` for implemented scope and verified checks. PWA packaging and a debug Android project scaffold are present; SMS/OTP, native health platforms, and several requested product pages still need implementation or external configuration.

## Tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest -q
```

## Project structure

```text
MediSense_Enhanced/
  backend/
    app/
      core/          # configuration and authentication
      database/      # SQLAlchemy models and session
      ml/             # topic classifier
      services/       # report extraction, analysis, assistant
      main.py         # API routes
    tests/
    seed_demo.py
  frontend/
    src/
      App.tsx
      index.css
      main.tsx
  docs/
  setup.bat
  start-backend.bat
  start-frontend.bat
  docker-compose.yml
```
\n## Docker (optional)\n\nCreate `backend/.env` from `.env.example`, then run `docker compose up --build`. The frontend is served on port 5173 and backend on port 8000. Docker setup is included as a convenience; validate it in your own environment before relying on it.\n

## Updated integrated frontend (AppJet merge)
The frontend entry point is wired to the merged authentication context, login/register screen, shared layout, and the Dashboard, AI Assistant, Report Analyzer, and Appointments page modules. Other existing workspace sections remain available through the legacy page implementations. The UI defaults to dark theme; use the theme control in the top bar to switch.

Run `setup.bat` once, then open two terminals and run `start-backend.bat` and `start-frontend.bat`. Open http://localhost:5173. Demo credentials are listed by the setup script and seeded backend output.
