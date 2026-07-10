# Error Contract — Release 2.0

## Standard error envelope

All STABLE `/api/v1/*` endpoints return errors in this structure:

```json
{
  "error": "Human-readable message",
  "code": "MACHINE_READABLE_CODE",
  "details": {},
  "correlation_id": "optional-request-id"
}
```

## HTTP status mapping

| Status | Use |
|--------|-----|
| 400 | Validation failure, malformed request |
| 401 | Missing or invalid authentication |
| 403 | Authenticated but not authorized |
| 404 | Resource not found (tenant-scoped) |
| 409 | Conflict (duplicate, invalid state transition) |
| 422 | Business rule violation |
| 429 | Rate limit exceeded |
| 500 | Unexpected server error (no internal details) |
| 501 | Feature not enabled (e.g. password reset without SMTP) |

## Rules

1. Never return stack traces or SQL errors to clients.
2. Never include secrets, tokens, or raw medical payloads in error `details`.
3. `correlation_id` should match request tracing when available.
4. State machine violations return **409** with code `INVALID_STATE_TRANSITION`.
5. Tenant isolation violations return **403** with code `TENANT_ACCESS_DENIED`.

## Legacy compatibility

Some older endpoints return `{"error": "message"}` only. New and updated endpoints must include `code`. Migration to full envelope is additive and does not break existing field `error`.
