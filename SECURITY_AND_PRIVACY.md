# Security and privacy notes

MediSense is an educational prototype. Do not upload real patient records or use it for clinical decisions.

## Implemented safeguards

- Passwords are stored as salted PBKDF2 hashes; API access uses signed bearer tokens.
- Patient-owned reports, appointments, metrics, medications, notifications, and other records are scoped to the authenticated user in the API.
- Admin APIs use server-side role checks. Frontend navigation visibility is not an authorization boundary.
- CORS origins are configurable. Uploads are size limited and file contents are parsed by document services rather than saved as public files.
- AI credentials are read by the backend only. Demo mode is the default and explicitly reported.
- The PWA precaches the app shell only. `/api` responses, user records, and tokens are not put in Workbox runtime caches.

## Before any shared deployment

- Set a random `SECRET_KEY`, production `ENVIRONMENT`, exact `CORS_ORIGINS`, TLS, and a managed PostgreSQL `DATABASE_URL`.
- Keep `.env`, databases, uploaded records, signing keys, and provider credentials out of version control.
- Add rate limiting, abuse monitoring, backups, retention/deletion rules, malware scanning, encryption-at-rest, consent flows, and incident response.
- The prototype stores the bearer token in browser localStorage. A production identity/session design should assess secure cookies, CSRF, refresh/rotation, and XSS risk.
- Review every role and ownership boundary, obtain a privacy/security assessment, and meet applicable law before handling real health data.

No claim of medical-device status, clinical validation, or production readiness is made.

## November 4 security verification

- Supabase Data API roles `anon` and `authenticated` have no table/sequence privileges in `public`; all 17 public tables have RLS enabled with no policies, which is deny-all. The FastAPI server accesses Postgres using its server-side connection and custom JWT, so this application does not rely on Supabase Auth row policies.
- The Supabase security advisor reports no security errors after the change. The remaining `rls_enabled_no_policy` INFO findings are intentional. Unused-index INFO notices remain untouched pending usage evidence.
- Production CORS is scoped to the deployed browser origin (same-origin) and Android's Capacitor origin `https://localhost`.
- Production startup now fails closed if `SECRET_KEY` is still the development default.

Residual controls and review still needed before any real health data: distributed rate limiting and abuse monitoring, identity/session and CSRF review, consent/retention/deletion policy, backup and incident response, privacy/legal review, and testing on physical Android devices. This is an educational prototype, not a clinical system.

