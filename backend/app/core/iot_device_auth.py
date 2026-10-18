"""Device authentication for IoT / logistics ingestion (P0-D).

Important:
- Devices are NOT authenticated like humans.
- We never trust device_id in the payload as identity.
- Identity is resolved from *credential headers*.
"""

from __future__ import annotations

import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

from flask import request
from sqlalchemy.exc import IntegrityError

from app.core.errors import build_error_response
from app.core.passwords import verify_password
from app.core.statuses import IOT_DEVICE_ACTIVE
from app.models.iot_device import IoTDevice
from app.models.iot_device_ingest_event import IoTDeviceIngestEvent


DEFAULT_IOT_DEVICE_INGEST_SECRET = "DXCON-IOT-INGEST-SECRET"

_DEVICE_ID_HEADERS = ("X-Device-Id", "X-Device-ID", "X-Device-ID".lower())
_DEVICE_CODE_HEADERS = ("X-Device-Code", "X-Device-Code".lower())
_DEVICE_SECRET_HEADERS = ("X-Device-Secret", "X-Device-API-Key", "X-Api-Key", "X-Device-Token")
_DEVICE_SIGNATURE_HEADER = "X-Device-Signature"

# Replay / integrity policy (production contract).
# - `event_id` OR `nonce` must be present for every ingestion request.
# - If `timestamp` is present, it must not be too far in the future, and must
#   not be arbitrarily old (prevents very old replayed measurements).
MAX_EVENT_FUTURE_SKEW_SECONDS = 300  # 5 minutes
MAX_EVENT_AGE_SECONDS = 86400  # 24 hours


@dataclass(frozen=True)
class AuthenticatedDevice:
    device: IoTDevice
    device_actor: str
    provided_secret: str


def _pick_header(keys: tuple[str, ...]) -> str | None:
    for k in keys:
        v = request.headers.get(k)
        if v:
            return v.strip()
    return None


def _require_secret(device: IoTDevice, provided_secret: str | None) -> bool:
    if not device.ingest_secret_hash:
        return False
    if not provided_secret:
        return False
    return verify_password(device.ingest_secret_hash, provided_secret)


def verify_request_signature(*, provided_secret: str, request_body: bytes) -> bool:
    """Verify optional device request signature when provided.

    Header: `X-Device-Signature` (hex)
    Signature: HMAC-SHA256(provided_secret, request_body_bytes).hexdigest()
    """
    sig = request.headers.get(_DEVICE_SIGNATURE_HEADER)
    if not sig:
        return True

    expected = hmac.new(
        provided_secret.encode("utf-8"),
        request_body,
        digestmod=sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, sig.strip())


def authenticate_iot_device() -> AuthenticatedDevice | tuple:
    """Return AuthenticatedDevice or an error response tuple."""
    device_id = _pick_header(_DEVICE_ID_HEADERS)
    device_code = _pick_header(_DEVICE_CODE_HEADERS)
    secret = _pick_header(_DEVICE_SECRET_HEADERS)

    if not device_id and not device_code:
        return build_error_response("UNAUTHORIZED", "Device credential required", 401)
    if not secret:
        return build_error_response("UNAUTHORIZED", "Device secret required", 401)

    device: IoTDevice | None = None
    if device_id:
        device = IoTDevice.query.filter_by(id=device_id).first()
    if not device and device_code:
        device = IoTDevice.query.filter_by(device_code=device_code).first()

    if not device:
        return build_error_response("UNAUTHORIZED", "Unknown device", 401)

    if device.status != IOT_DEVICE_ACTIVE:
        return build_error_response("FORBIDDEN", "Device is disabled", 403)

    if not _require_secret(device, secret):
        return build_error_response("FORBIDDEN", "Invalid device credentials", 403)

    actor = f"device:{device.device_code}"
    # If a signature header is present, verify it against the request body.
    request_body = request.get_data(cache=False) or b""
    if not verify_request_signature(provided_secret=secret, request_body=request_body):
        return build_error_response("FORBIDDEN", "Invalid device signature", 403)

    return AuthenticatedDevice(device=device, device_actor=actor, provided_secret=secret)


def validate_device_identity_and_bind_payload(
    *,
    device: IoTDevice,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], tuple | None]:
    """Ensure payload claims do not override the authenticated device.

    - If payload contains device_id/deviceId and differs → reject.
    - If payload missing device_id, bind it to authenticated device.
    - If payload contains partner_id/organization_id and mismatches device.partner_id → reject.
    """
    payload = dict(payload or {})

    payload_device_id = payload.get("device_id") or payload.get("deviceId")
    if payload_device_id and str(payload_device_id) != str(device.id):
        return payload, build_error_response("FORBIDDEN", "device_id mismatch", 403)

    payload["device_id"] = device.id

    # Tenant binding for IoT ingestion:
    # - The only canonical field we currently have on `IoTDevice` is `partner_id`.
    # - IoT ingestion must never treat `organization_id` as equivalent unless
    #   we have an explicit mapping model (none exists in current code).
    payload_partner = payload.get("partner_id") or payload.get("partnerId")
    if payload.get("organization_id") is not None or payload.get("organizationId") is not None:
        return payload, build_error_response("FORBIDDEN", "organization_id selector not allowed", 403)

    expected = device.partner_id
    if expected and payload_partner and str(payload_partner) != str(expected):
        return payload, build_error_response("FORBIDDEN", "partner_id mismatch", 403)
    return payload, None


def extract_event_id(payload: dict[str, Any]) -> str | None:
    return (
        payload.get("event_id")
        or payload.get("device_event_id")
        or payload.get("message_id")
        or payload.get("idempotency_key")
    )


def extract_nonce(payload: dict[str, Any]) -> str | None:
    return payload.get("nonce") or payload.get("request_nonce")


def extract_event_timestamp(payload: dict[str, Any]) -> datetime | None:
    raw = payload.get("timestamp") or payload.get("event_timestamp") or payload.get("recorded_at")
    if raw is None or raw == "":
        return None
    # Accept epoch seconds or ISO8601.
    try:
        if isinstance(raw, (int, float)) or (isinstance(raw, str) and raw.isdigit()):
            ts = float(raw)
            return datetime.fromtimestamp(ts, tz=timezone.utc)
    except (TypeError, ValueError, OSError, OverflowError):
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except Exception:
        return None

def validate_event_timestamp(ts: datetime) -> tuple[bool, str | None]:
    """Return (ok, error_message_if_any)."""
    if not ts:
        return True, None
    now = datetime.now(tz=timezone.utc)
    if ts > (now + timedelta(seconds=MAX_EVENT_FUTURE_SKEW_SECONDS)):
        return False, "Event timestamp too far in the future"
    if ts < (now - timedelta(seconds=MAX_EVENT_AGE_SECONDS)):
        return False, "Event timestamp too old"
    return True, None


def compute_payload_hash(payload: dict[str, Any]) -> str:
    return sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def require_event_identifier(payload: dict[str, Any]) -> tuple[dict[str, Any], str | None, str | None] | tuple:
    """Require deterministic anti-replay inputs.

    Production rule: Every ingestion must include either `event_id` (or alias)
    or `nonce` (or alias).
    """
    payload = dict(payload or {})
    event_id = extract_event_id(payload)
    nonce = extract_nonce(payload)
    if not event_id and not nonce:
        return build_error_response(
            "BAD_REQUEST",
            "event_id or nonce is required for ingestion replay protection",
            400,
        )
    return payload, event_id, nonce


def ingest_idempotency_guard(
    *,
    device_id: str,
    payload: dict[str, Any],
    event_id: str | None,
    nonce: str | None,
) -> tuple[str, dict[str, Any] | None]:
    """Atomic idempotency/replay guard using DB uniqueness constraints.

    Returns:
      ("process", None)
      ("already_processed", {"already_processed": True})
      ("replay_rejected", {"replay_rejected": True})
      ("idempotency_conflict", None)
    """
    payload_hash = compute_payload_hash(payload)
    row = IoTDeviceIngestEvent(
        device_id=str(device_id),
        event_id=str(event_id) if event_id else None,
        nonce=str(nonce) if nonce else None,
        payload_hash=payload_hash,
        processed=True,
    )

    try:
        # Insert and flush early so concurrency is handled by DB constraints.
        db_session = IoTDeviceIngestEvent.query.session
        db_session.add(row)
        db_session.flush()
        db_session.commit()
        return "process", None
    except IntegrityError:
        db_session = IoTDeviceIngestEvent.query.session
        db_session.rollback()

        # Prefer lookup by event_id when present; it's the idempotency key.
        if event_id:
            existing = IoTDeviceIngestEvent.query.filter_by(device_id=str(device_id), event_id=str(event_id)).first()
            if existing and existing.payload_hash == payload_hash:
                return "already_processed", {"already_processed": True, "event_id": event_id}
            return "idempotency_conflict", None

        if nonce:
            existing_nonce = IoTDeviceIngestEvent.query.filter_by(device_id=str(device_id), nonce=str(nonce)).first()
            if existing_nonce:
                return "replay_rejected", {"replay_rejected": True, "nonce": nonce}
        return "idempotency_conflict", None

