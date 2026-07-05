# Device Gateway Architecture (Phase 7.5)

## Purpose

Central hub for laboratory device connectivity: HL7/TCP listeners, ASTM scaffold, and adapter registry.

## Components

- **Hub:** `/device-gateway`
- **API:** `/api/v1/device-gateway/*`
- **HL7/TCP:** existing `/api/v1/hl7/*` routes
- **Adapters:** `app.adapters` framework

## ASTM Status

ASTM adapter is **scaffold** — HL7/TCP paths are production-ready.

## Verification

`python scripts/verify_device_gateway.py`
