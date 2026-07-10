# Integration Contract Freeze — Release 2.0

Frozen per Epic 3.5 (`app/integration/`).

## Connector interface

`ConnectorAdapter` methods: `test_connection`, `pull_orders`, `push_orders`, `pull_results`, `push_results`, `acknowledge_message`, `transform_inbound`, `transform_outbound`, `health_check`

## Production-ready protocols

- CSV, JSON, WEBHOOK, MANUAL

## Foundation-only protocols

- REST, HL7 v2, FHIR R4, SFTP (must not falsely report production readiness)

## Idempotency

Unique constraint: `(connector_id, external_message_id, message_type)`

## Webhook signature

HMAC-SHA256 over `timestamp.payload_hash` with delivery ID and replay window.

## Retry / dead-letter

DB-backed queue; strategies `FIXED`, `EXPONENTIAL_BACKOFF`; dead-letter after max retries.

## API credential scopes

`patients.read`, `orders.read/write`, `samples.read`, `results.read/write`, `reports.read`, `webhooks.manage`

## Audit

`intg_audit_events` — connector, message, webhook, credential events.

## Verification

`INTEGRATION_FREEZE_REPORT.json`, `verify_integration_platform.py`
