# Deployment guide

The repository is a local-development prototype. A public shareable site requires separately provisioned frontend hosting, backend hosting, PostgreSQL, HTTPS, and production environment variables.

## Frontend

- Build with `cd frontend && npm ci && npm run build`.
- Publish `frontend/dist` through a static host with SPA fallback to `index.html`.
- Configure the host/API proxy to send `/api/*` to the backend origin. Set a narrow backend `CORS_ORIGINS` allowlist.
- The generated PWA service worker precaches static app-shell assets only; API responses are excluded.

## Backend

- Deploy the FastAPI app from `backend` with `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (adapt the launch command to the provider).
- Set `SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`, `ENVIRONMENT=production`, upload limits, and optional AI credentials as provider secrets.
- Apply migrations with Alembic and provision backups before deployment. Do not use the demo SQLite database for a shared environment.
- Verify `/api/health`, login, upload limits, and owner isolation after deployment.

Do not upload real patient data to this demo. No live deployment or public URL is configured by this project copy.
