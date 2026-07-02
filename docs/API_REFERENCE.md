# DxCon API Reference

See also `docs/API_OVERVIEW.md` for domain groupings.

## Base URL

- Development: `http://localhost:5000`
- Production: configured via ingress (`https://api.example.com`)

## Authentication

- JWT bearer tokens via `/api/v1/auth/login` and `/api/v1/auth/refresh`
- API keys via `/api/v1/api-keys` (platform clients)

## Standard Response Envelope

```json
{
  "success": true,
  "data": {},
  "request_id": "uuid",
  "timestamp": "ISO-8601"
}
```

Error responses include `success: false` and an `error` object with `code`, `message`, and optional `field`.

## OpenAPI

- JSON: `GET /api/v1/openapi.json`
- YAML: `GET /api/v1/openapi.yaml`

## Pagination

List endpoints accept `page`, `page_size`, `sort`, and filter parameters via `backend/app/core/list_params.py`.

## Health Endpoints (Public)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/system/health` | Application health |
| GET | `/api/v1/system/ready` | Readiness probe |
| GET | `/api/v1/system/live` | Liveness probe |

## Verification

```bash
cd backend
./venv/bin/python scripts/verify_enterprise_hardening_pack4.py
```

Generated reports: `backend/generated_release/api_review.json`, `openapi_validation.json`, `api_consistency.json`
