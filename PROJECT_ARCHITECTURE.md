# MediSense Architecture

## High-level flow

Browser (React + TypeScript + Vite)
→ Axios API client (`/api`)
→ FastAPI routes
→ Authentication / service layer
→ SQLAlchemy ORM
→ SQLite (default) or PostgreSQL (configured through DATABASE_URL)

## Frontend

- React Router controls the dashboard sections.
- Reusable UI primitives (`Card`, `Heading`, `Tag`, `Stat`, `Empty`) keep visual patterns consistent.
- Recharts renders dashboard and insights charts.
- Framer Motion adds restrained route transitions.
- Axios request interceptor attaches the JWT stored in browser localStorage.
- CSS design tokens support light and dark themes.

## Backend

- `core/config.py`: environment configuration.
- `core/security.py`: password hashing and JWT helpers.
- `database/models.py`: SQLAlchemy tables.
- `services/report_extraction.py`: PDF text extraction and parameter parsing.
- `services/report_analysis.py`: flags against only report-supplied ranges.
- `services/ai_service.py`: transparent deterministic demo assistant.
- `ml/classification.py`: TF-IDF + logistic regression topic routing.
- `main.py`: REST API, auth dependencies, role checks and endpoints.

## Data ownership

Patient-facing record queries filter by authenticated `user_id`. Report detail lookup is owner-scoped. Doctor/admin workflows are deliberately limited in this prototype; do not treat the current role scaffolding as a complete hospital-grade access model.

## Security notes

JWT secret must be changed before deployment. HTTPS, secure token storage, CSRF strategy, encryption at rest, malware scanning, audit retention, rate limiting, consent and data deletion workflows require additional production engineering.
