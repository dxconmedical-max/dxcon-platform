# IoT Security Model

## Authentication

- **Staff APIs**: session or JWT with role checks (`COLLECTOR`, `LAB`, `OPERATIONS`, `ADMIN`).
- **Device ingest**: `X-Device-ID` + `X-Device-Token`; credentials stored as SHA-256 hashes only.

## Tenant isolation

All platform queries filter by `organization_id`. Cross-tenant device or trip access returns not found.

## Payload safety

- PHI keys rejected in telemetry payloads.
- Payload size limits and rate limiting foundation in ingestion module.
- Replay protection via idempotency keys and sequence validation.

## Production guards

IoT simulator requires `IOT_SIMULATOR_ENABLED` and cannot run silently in production.
