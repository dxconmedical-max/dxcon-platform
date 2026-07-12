"""Canonical telemetry ingestion — vendor-neutral gateway foundation."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any

from app.extensions.db import db
from app.iot_platform.auth import hash_device_secret, simulator_allowed
from app.models.iot_device import IoTDevice
from app.models.iot_platform import (
    IoTCanonicalReading,
    IoTDeviceCredential,
    IoTTelemetryDeadLetter,
)


class IngestionError(ValueError):
    pass


MAX_PAYLOAD_BYTES = 64_000
TIMESTAMP_TOLERANCE_SECONDS = 600
REQUIRED_FIELDS = ("device_id", "recorded_at")


def _parse_ts(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00").replace("+00:00", ""))
    raise IngestionError("Invalid recorded_at")


def validate_canonical_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if len(json.dumps(payload, default=str)) > MAX_PAYLOAD_BYTES:
        raise IngestionError("Payload too large")
    for field in REQUIRED_FIELDS:
        if field not in payload or payload[field] in (None, ""):
            raise IngestionError(f"Missing required field: {field}")
    # PHI guard — reject common clinical identifiers in payload keys/values
    forbidden = ("patient_name", "phone", "mrn", "diagnosis")
    lower = json.dumps(payload).lower()
    for token in forbidden:
        if token in lower:
            raise IngestionError("PHI not permitted in device payload")
    recorded = _parse_ts(payload["recorded_at"])
    now = datetime.utcnow()
    if abs((now - recorded).total_seconds()) > TIMESTAMP_TOLERANCE_SECONDS:
        raise IngestionError("Timestamp outside tolerance window")
    return payload


def _idempotency_key(payload: dict[str, Any]) -> str:
    device_id = payload["device_id"]
    seq = payload.get("sequence_number")
    recorded = str(payload.get("recorded_at"))
    raw = f"{device_id}|{seq}|{recorded}"
    return hashlib.sha256(raw.encode()).hexdigest()


def ingest_telemetry(
    payload: dict[str, Any],
    *,
    organization_id: str,
    adapter_type: str = "HTTP_JSON",
    simulated: bool = False,
) -> dict[str, Any]:
    if simulated and not simulator_allowed():
        raise IngestionError("Simulator disabled in this environment")

    validate_canonical_payload(payload)
    device = IoTDevice.query.get(payload["device_id"])
    if not device:
        raise IngestionError("Unknown device")

    idem = _idempotency_key(payload)
    if IoTCanonicalReading.query.filter_by(idempotency_key=idem).first():
        return {"status": "duplicate", "idempotency_key": idem}

    seq = payload.get("sequence_number")
    if seq is not None:
        last = (
            IoTCanonicalReading.query.filter_by(device_id=payload["device_id"])
            .order_by(IoTCanonicalReading.sequence_number.desc())
            .first()
        )
        if last and last.sequence_number is not None and seq <= last.sequence_number:
            raise IngestionError("Out-of-order sequence rejected")

    reading = IoTCanonicalReading(
        organization_id=organization_id,
        device_id=payload["device_id"],
        idempotency_key=idem,
        sequence_number=seq,
        recorded_at=_parse_ts(payload["recorded_at"]),
        temperature_c=payload.get("temperature_c"),
        humidity_percent=payload.get("humidity_percent"),
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
        speed_kph=payload.get("speed_kph"),
        heading=payload.get("heading"),
        altitude_m=payload.get("altitude_m"),
        battery_percent=payload.get("battery_percent"),
        signal_strength=payload.get("signal_strength"),
        door_open=payload.get("door_open"),
        trip_id=payload.get("trip_id"),
        transport_container_id=payload.get("transport_container_id"),
        metadata_json=json.dumps(payload.get("metadata") or {}),
        simulated=simulated,
    )
    db.session.add(reading)
    device.last_seen_at = datetime.utcnow()
    if payload.get("battery_percent") is not None and hasattr(device, "battery_level"):
        device.battery_level = int(payload["battery_percent"])
    db.session.flush()
    return {"status": "accepted", "reading_id": reading.id, "simulated": simulated}


def record_dead_letter(
    *,
    organization_id: str | None,
    device_id: str | None,
    adapter_type: str,
    error_code: str,
    error_message: str,
    payload_ref: str | None = None,
) -> None:
    db.session.add(
        IoTTelemetryDeadLetter(
            organization_id=organization_id,
            device_id=device_id,
            adapter_type=adapter_type,
            error_code=error_code,
            error_message=error_message,
            payload_ref=payload_ref,
        )
    )


def provision_device_credential(device_id: str, secret: str | None = None) -> dict[str, str]:
    """Create credential — secret returned once, never stored in plaintext."""
    token = secret or uuid.uuid4().hex
    db.session.add(
        IoTDeviceCredential(
            device_id=device_id,
            credential_hash=hash_device_secret(token),
            credential_ref=f"ref-{device_id[:8]}",
        )
    )
    return {"device_id": device_id, "token": token, "note": "Store token securely; not retrievable again"}
