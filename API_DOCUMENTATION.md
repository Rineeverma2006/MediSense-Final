# API reference

Base URL: `http://localhost:8000/api`

Interactive OpenAPI docs: `/docs`

Authentication: send `Authorization: Bearer <access_token>` after login.

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | No | Health check |
| POST | `/auth/register` | No | Create patient account |
| POST | `/auth/login` | No | Obtain JWT |
| GET | `/auth/me` | Yes | Current user |
| POST | `/reports/analyze` | Patient/doctor | Upload and analyze PDF |
| GET | `/reports` | Yes | Current user's report list |
| GET | `/reports/{id}` | Yes | Owner-scoped report detail |
| POST | `/assistant` | Yes | Demo assistant response |
| GET/POST | `/appointments` | Yes | List/create appointments |
| PATCH | `/appointments/{id}/cancel` | Yes | Cancel own appointment |
| GET/POST | `/medications` | Yes | List/add own medications |
| PATCH | `/medications/{id}/toggle` | Yes | Toggle own medication active state |
| GET/POST | `/metrics` | Yes | List/add own metrics |
| GET | `/doctors` | No | Demo doctor directory |
| GET | `/health-records` | Yes | Own report archive |
| GET | `/analytics/summary` | Yes | Own record counts |
| GET | `/admin/audit` | Admin | Recent audit events |

## Example login

```json
POST /api/auth/login
{"email":"patient@medisense.demo","password":"MediSense@123"}
```

Returns `access_token`, `token_type`, `role`, and `name`.

## Report upload

Multipart form field name: `file`. PDF only, maximum 5 MB. The current parser expects text-based PDFs and supported line formats. A report with no extracted parameters returns HTTP 422.

## Medical safety

The report analyzer does not infer diagnoses or invent reference ranges. A status means only below/above/within the range printed in that specific document.
