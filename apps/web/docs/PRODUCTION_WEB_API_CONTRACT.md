# DxCon Production Web API Contract

Production API base: `https://api.dxcon.com.vn`

This document maps verified backend endpoints used by the `apps/web` production pilot. Do not invent endpoints beyond this contract.

## Environment

| Variable | Production value |
|----------|------------------|
| `NEXT_PUBLIC_API_BASE_URL` | `https://api.dxcon.com.vn` |
| `NEXT_PUBLIC_PUBLIC_SITE_URL` | `https://dxcon.com.vn` |
| `NEXT_PUBLIC_APP_URL` | `https://app.dxcon.com.vn` |
| `NEXT_PUBLIC_APP_ENV` | `production` |
| `NEXT_PUBLIC_DEMO_MODE` | `false` |

## Authentication

All auth routes are under `/api/v1/auth`. See also [AUTH_API_CONTRACT.md](./AUTH_API_CONTRACT.md).

| Capability | Method | Path | Auth |
|------------|--------|------|------|
| Login | POST | `/api/v1/auth/login` | None |
| Logout / token revocation | POST | `/api/v1/auth/logout` | Bearer refresh token |
| Refresh access token | POST | `/api/v1/auth/refresh` | Bearer refresh token |
| Current user + session | GET | `/api/v1/auth/me` | Bearer access token |
| Memberships (organizations) | GET | `/api/v1/auth/memberships` | Bearer access token |
| Switch active organization | POST | `/api/v1/auth/switch-organization` | Bearer access token |
| Permissions + features | GET | `/api/v1/auth/capabilities` | Bearer access token |
| Forgot password | POST | `/api/v1/auth/forgot-password` | None (may return 501) |
| Reset password | POST | `/api/v1/auth/reset-password` | None (may return 501) |

### Request headers (authenticated calls)

- `Authorization: Bearer <access_token>`
- `X-Organization-ID: <uuid>` when organization context is required
- `X-Correlation-ID: <uuid>` for tracing

## Organizations

There is no standalone public organization list for the web pilot. Organization context is resolved via:

1. `GET /api/v1/auth/me` → `active_organization_id`
2. `GET /api/v1/auth/memberships` → organization metadata per membership
3. `POST /api/v1/auth/switch-organization` → updated capabilities

## Permissions and feature flags

`GET /api/v1/auth/capabilities` returns:

```json
{
  "success": true,
  "data": {
    "user": { "id", "email", "role", "organization_id" },
    "organization": { "id", "organization_code", "organization_name", "organization_type", "status" },
    "membership": { "membership_id", "organization_id", "role_code", "membership_status" },
    "workspace": "/app/doctor",
    "default_workspace": "/app/doctor",
    "permissions": ["portal.doctor.read"],
    "features": []
  }
}
```

## Workspace dashboards

| Workspace | Endpoint |
|-----------|----------|
| Reception | `GET /api/v1/reception-workspace/dashboard` |
| Executive | `GET /api/v1/executive-platform/dashboard` |
| Laboratory | `GET /api/v1/lab/dashboard` |
| Doctor portal | `GET /api/v1/doctor-portal/dashboard` |
| Patient portal | `GET /api/v1/portal/patient/dashboard` |
| Operations (pilot) | `GET /api/v1/pilot-readiness/health-dashboard` |

All dashboard endpoints require authentication and organization context.

## Clinical data (backend ready; web wiring incremental)

| Domain | Endpoints |
|--------|-----------|
| Patients | `GET/POST /api/v1/patients`, `POST /api/v1/reception-workspace/patients/register`, `GET /api/v1/reception-workspace/patients/<code>` |
| Orders | `GET/POST /api/v1/orders`, `POST /api/v1/reception-workspace/orders` |
| Samples | `GET/POST /api/v1/sample-trackings`, `GET/POST /api/v1/sample-collections` |
| Results | `GET /api/v1/results`, `GET /api/v1/test-results` |
| Reports | `GET /api/v1/reports`, `GET /api/v1/portal/patient/reports/<code>`, `GET /api/v1/portal/doctor/reports/<code>` |

## System health

| Endpoint | Purpose | Auth |
|----------|---------|------|
| `GET /health` | Liveness / deployment smoke | None |
| `GET /ready` | Readiness probe | None |
| `GET /live` | Live probe | None |
| `GET /api/v1/system/health` | Detailed system status | Ops |

The web client uses `GET /health` for connectivity checks.

## Public metrics

No approved unauthenticated public metrics endpoint exists for the marketing site. Landing page statistics must not call production clinical counters. Use illustrative capability cards or label content as preview-only.

## CORS

Browser requests from the web app require backend `CORS_ORIGINS` to include:

- `https://dxcon.com.vn`
- `https://www.dxcon.com.vn`
- `https://app.dxcon.com.vn`
- Vercel preview deployment origins (during rollout)

CORS changes are backend configuration only; do not weaken tenant isolation or authorization.

## API client location

| Module | Role |
|--------|------|
| `src/lib/api/client.ts` | Typed HTTP client |
| `src/lib/api/auth.ts` | Auth endpoints |
| `src/lib/api/health.ts` | Health checks |
| `src/lib/api/workspaces.ts` | Workspace dashboard endpoints |
| `src/services/api.ts` | Compatibility re-export |
| `src/services/auth.ts` | Compatibility re-export |

## Error envelope

Failed responses return JSON with `error` and optional `code`:

```json
{ "error": "Invalid credentials", "code": "AUTH_INVALID" }
```

The client maps these to `ApiError` without logging tokens or PHI.
