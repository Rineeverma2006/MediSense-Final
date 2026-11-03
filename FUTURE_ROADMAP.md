# MediSense Future Roadmap

## Priority 1 — Complete engineering baseline
- Add dedicated registration UI and password reset workflow.
- Add API integration tests for every endpoint and authorization boundary.
- Add proper migrations with Alembic.
- Add a shared API error/loading layer and form validation.
- Replace sample chart data with authenticated `/metrics` data.
- Add server-side pagination and filtering.

## Priority 2 — Advanced healthcare workflows
- OCR pipeline for scanned PDFs with user confirmation of extracted values.
- Robust lab-specific parsing and extraction confidence scores.
- Report comparison UI with unit normalization and source provenance.
- Clinician-approved educational content retrieval with citations.
- Appointment time-slot availability and notification integration.
- Doctor portal with explicit patient consent and scoped access.

## Priority 3 — Production readiness
- PostgreSQL deployment, migrations and automated backups.
- Object storage with malware scanning and encryption.
- Short-lived access tokens, refresh tokens and secure cookie strategy.
- Rate limiting, monitoring, structured logs and security tests.
- Privacy impact assessment, consent, retention/deletion and legal review.
- Clinical validation and regulatory assessment before any decision-support claims.
