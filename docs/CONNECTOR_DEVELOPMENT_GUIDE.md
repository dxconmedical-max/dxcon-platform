# Connector Development Guide

## Adding a Vendor Connector

1. Register connector via `POST /api/v1/integration/connectors`
2. Choose `protocol` (CSV, JSON, REST, HL7_V2, FHIR_R4, etc.)
3. Configure mapping rules via `POST /api/v1/integration/mappings`
4. Map external test codes before production import
5. Test connection via `POST /api/v1/integration/connectors/{id}/test`

## Adapter Interface

Implement `ConnectorAdapter` in `backend/app/integration/adapters/`:

- `test_connection()`, `health_check()`
- `transform_inbound()`, `transform_outbound()`
- Optional: `pull_orders()`, `push_results()`, etc.

Do not add vendor logic to clinical business modules.

## Foundation vs Production

Adapters set `production_ready = True` only when fully operational. HL7, FHIR, REST polling, and SFTP are foundation-only in Epic 3.5.
