# DxCon Integration Architecture (Epic 3.5)

## Overview

The integration platform at `backend/app/integration/` provides a vendor-neutral connector framework for exchanging healthcare data with external systems.

Production API: `https://api.dxcon.com.vn/api/v1/integration`

## Layers

1. **Connector Registry** — organization-scoped connectors (`intg_connectors`)
2. **Adapters** — protocol-specific transforms (CSV/JSON operational; HL7/FHIR/REST/SFTP foundation)
3. **Mapping Engine** — configurable field and code mappings
4. **Inbound Pipeline** — receive → validate → idempotency → transform → stage → audit
5. **Outbound Pipeline** — domain events → webhooks → delivery attempts
6. **LIS Bridge** — CSV/JSON imports delegate to `lab_workspace/lis_service.py` (validation required, no auto-release)

## Canonical Model

Internal payloads are normalized to canonical Patient, Order, Sample, Result, and Report shapes before business processing.

## Security

- JWT authentication on all integration APIs
- Organization tenant isolation
- SSRF protection on webhook endpoints
- Masked payload previews in message records
- Secret references only (no raw secrets in DB)

## Related Docs

- `CONNECTOR_DEVELOPMENT_GUIDE.md`
- `LIS_INTEGRATION_GUIDE.md`
- `WEBHOOK_GUIDE.md`
- `PARTNER_API_SECURITY.md`
