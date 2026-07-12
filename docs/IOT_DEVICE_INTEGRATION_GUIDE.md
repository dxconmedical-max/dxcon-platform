# IoT Device Integration Guide

Release 7.0 Sprint 4 — vendor-neutral device onboarding and telemetry.

## Device registry

Register devices via `POST /api/v1/iot/devices` with organization scope. Provisioning returns a one-time device token; credentials are stored hashed and never returned again.

Supported device types: temperature sensor, temperature/humidity sensor, GPS tracker, cold-chain tracker, door sensor, BLE gateway, mobile collector device, vehicle gateway.

## Telemetry ingestion

`POST /api/v1/iot/telemetry` with headers:

- `X-Device-ID`
- `X-Device-Token`
- `X-IoT-Adapter` (HTTP_JSON, MQTT, WEBHOOK, BLE_GATEWAY, BATCH_UPLOAD, SIMULATOR)

Canonical payload fields: `device_id`, `recorded_at`, optional temperature, humidity, GPS, battery, door, trip and container references. **No PHI.**

## Adapters

The ingestion gateway validates schema, enforces idempotency, sequence ordering, timestamp tolerance, and dead-letter logging. Vendor-specific adapters plug in without changing clinical workflows.

## Simulator

`python backend/scripts/simulate_iot_trip.py` — disabled in production unless explicitly forced. All simulated readings are labelled `SIMULATED`.
