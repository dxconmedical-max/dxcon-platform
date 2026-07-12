# IoT Mobile Integration Contract

Release 7.0 Sprint 4 — API contracts for mobile collectors (no mobile app changes in this sprint).

## Endpoints

| Capability | Method | Path |
|------------|--------|------|
| Background GPS / telemetry upload | POST | `/api/v1/iot/telemetry` |
| Trip list | GET | `/api/v1/logistics/trips` |
| Trip transition (start/complete) | POST | `/api/v1/logistics/trips/{id}/transition` |
| Custody event | POST | `/api/v1/custody/events` |
| Offline buffer (existing) | GET/POST | `/api/v1/iot-logistics/offline-buffer` |

## Headers

```
X-Device-ID: <uuid>
X-Device-Token: <provisioning token>
X-Organization-ID: <tenant>
X-IoT-Adapter: BLE_GATEWAY | HTTP_JSON
```

## Offline queue

Mobile clients should queue canonical readings locally and batch upload with monotonic `sequence_number`. Duplicates are acknowledged without double-counting.

## Scan flows

Container and specimen scans should emit custody events (`container_sealed`, `specimen_collected`) with `reference_type` / `reference_id` — no patient identifiers in device payloads.
