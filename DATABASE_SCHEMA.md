# Database schema

- `users`: email, name, role, password hash, created timestamp.
- `reports`: owner user ID, filename, extracted analysis JSON, created timestamp.
- `appointments`: owner user ID, doctor label, specialty, appointment time, status, notes.
- `medications`: owner user ID, name, dosage, frequency, dates, active flag.
- `health_metrics`: owner user ID, metric label, value, unit, recorded date.
- `audit_logs`: actor user ID, action, timestamp.

The default database is SQLite and tables are created at application startup. Alembic is configured with an initial schema revision in `migrations/versions/`. Run `alembic upgrade head` from the backend directory to apply migrations. For production, use PostgreSQL, indexes appropriate to query patterns, backups and retention controls.
