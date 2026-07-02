# DxCon API Overview

## Versioning

Primary REST surface: `/api/v1/*`

Additional versioned areas:

- `/api/v2/ai` — legacy AI v2 routes
- `/api/v1/ai-v2` — interpretation batch endpoints
- `/api/v1/ai-platform` — advisory AI platform foundation

## Response Format

API routes under `/api/` use a JSON envelope when `API_RESPONSE_ENVELOPE=true`.

Errors are standardized through `backend/app/core/errors.py` with stable status codes:

- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found
- 409 Conflict
- 422 Unprocessable Entity
- 429 Rate Limited
- 500 Internal Server Error

## Major API Groups

| Prefix | Purpose |
|--------|---------|
| `/api/v1/auth` | Authentication |
| `/api/v1/files` | File upload/download/metadata |
| `/api/v1/system` | Health, storage, queue diagnostics |
| `/api/v1/ai-platform` | AI providers, prompts, inference, audit |
| `/api/v1/connectors` | Integration connector registry |
| `/api/v1/integrations` | Legacy gateway plus platform audit/sandbox token |
| `/api/v1/webhooks` | Integration webhook engine |
| `/api/v1/events` | Integration domain events |

## Headers

- `X-Request-ID` — per-request identifier
- `X-Correlation-ID` — propagated correlation identifier
- `X-Trace-ID` — trace identifier for observability
- `X-Tenant-ID` — tenant context when available

## Safety Constraints

- AI platform endpoints are advisory-only and require human review flags in responses
- Signed URLs and webhook signatures use HMAC-based verification
- Sensitive request values must not appear in logs

## Inventory Verification

Run:

```bash
python backend/scripts/verify_blueprint_registry.py
python backend/scripts/verify_route_inventory.py
```

These checks validate route registration and duplicate-route detection without changing API contracts.
