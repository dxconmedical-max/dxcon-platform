from flask import Blueprint, request

from app.core.authenticated_identity import require_authenticated_user
from app.core.iot_device_auth import (
    authenticate_iot_device,
    extract_event_id,
    extract_event_timestamp,
    extract_nonce,
    ingest_idempotency_guard,
    validate_device_identity_and_bind_payload,
    validate_event_timestamp,
)

from app.services.iot_cold_chain_service import (
    ColdChainAlertService,
    ColdChainService,
    GPSMonitoringService,
    IoTDeviceService,
    IoTError,
    TemperatureMonitoringService,
)


iot_bp = Blueprint(
    "iot",
    __name__,
    url_prefix="/api/v1/iot",
)


@iot_bp.route("/devices", methods=["GET"])
@require_authenticated_user
def list_devices():
    payload = IoTDeviceService.list_devices(
        status=request.args.get("status"),
        device_type=request.args.get("device_type"),
    )
    return payload


@iot_bp.route("/devices", methods=["POST"])
@require_authenticated_user
def register_device():
    data = request.get_json(silent=True) or {}
    try:
        payload = IoTDeviceService.register_device(data)
    except IoTError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Device registered", **payload}, 201


@iot_bp.route("/readings/temperature", methods=["POST"])
def record_temperature():
    data = request.get_json(silent=True) or {}
    auth = authenticate_iot_device()
    if isinstance(auth, tuple):
        return auth
    device = auth.device
    data, err = validate_device_identity_and_bind_payload(device=device, payload=data)
    if err is not None:
        return err
    event_id = extract_event_id(data)
    nonce = extract_nonce(data)
    ts = extract_event_timestamp(data)
    if ts:
        ok, msg = validate_event_timestamp(ts)
        if not ok:
            return {"error": msg}, 400
    if not event_id and not nonce:
        return {"error": "event_id or nonce is required for ingestion replay protection"}, 400
    action, meta = ingest_idempotency_guard(
        device_id=device.id,
        payload=data,
        event_id=event_id,
        nonce=nonce,
    )
    if action == "already_processed":
        return {"message": "Duplicate event ignored", **(meta or {}), "already_processed": True}, 200
    if action == "replay_rejected":
        raise IoTError("Replay request (nonce already used)", 409)
    if action == "idempotency_conflict":
        raise IoTError("Idempotency conflict (payload differs)", 409)
    try:
        payload = TemperatureMonitoringService.record_temperature(data)
    except IoTError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Temperature recorded", **payload}, 201


@iot_bp.route("/readings/humidity", methods=["POST"])
def record_humidity():
    data = request.get_json(silent=True) or {}
    auth = authenticate_iot_device()
    if isinstance(auth, tuple):
        return auth
    device = auth.device
    data, err = validate_device_identity_and_bind_payload(device=device, payload=data)
    if err is not None:
        return err
    event_id = extract_event_id(data)
    nonce = extract_nonce(data)
    ts = extract_event_timestamp(data)
    if ts:
        ok, msg = validate_event_timestamp(ts)
        if not ok:
            return {"error": msg}, 400
    if not event_id and not nonce:
        return {"error": "event_id or nonce is required for ingestion replay protection"}, 400
    action, meta = ingest_idempotency_guard(
        device_id=device.id,
        payload=data,
        event_id=event_id,
        nonce=nonce,
    )
    if action == "already_processed":
        return {"message": "Duplicate event ignored", **(meta or {}), "already_processed": True}, 200
    if action == "replay_rejected":
        raise IoTError("Replay request (nonce already used)", 409)
    if action == "idempotency_conflict":
        raise IoTError("Idempotency conflict (payload differs)", 409)
    try:
        payload = TemperatureMonitoringService.record_humidity(data)
    except IoTError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Humidity recorded", **payload}, 201


@iot_bp.route("/readings/gps", methods=["POST"])
def record_gps():
    data = request.get_json(silent=True) or {}
    auth = authenticate_iot_device()
    if isinstance(auth, tuple):
        return auth
    device = auth.device
    data, err = validate_device_identity_and_bind_payload(device=device, payload=data)
    if err is not None:
        return err
    event_id = extract_event_id(data)
    nonce = extract_nonce(data)
    ts = extract_event_timestamp(data)
    if ts:
        ok, msg = validate_event_timestamp(ts)
        if not ok:
            return {"error": msg}, 400
    if not event_id and not nonce:
        return {"error": "event_id or nonce is required for ingestion replay protection"}, 400
    action, meta = ingest_idempotency_guard(
        device_id=device.id,
        payload=data,
        event_id=event_id,
        nonce=nonce,
    )
    if action == "already_processed":
        return {"message": "Duplicate event ignored", **(meta or {}), "already_processed": True}, 200
    if action == "replay_rejected":
        raise IoTError("Replay request (nonce already used)", 409)
    if action == "idempotency_conflict":
        raise IoTError("Idempotency conflict (payload differs)", 409)
    try:
        payload = GPSMonitoringService.record_gps(data)
    except IoTError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "GPS recorded", **payload}, 201


@iot_bp.route("/readings/shock", methods=["POST"])
def record_shock():
    data = request.get_json(silent=True) or {}
    auth = authenticate_iot_device()
    if isinstance(auth, tuple):
        return auth
    device = auth.device
    data, err = validate_device_identity_and_bind_payload(device=device, payload=data)
    if err is not None:
        return err
    event_id = extract_event_id(data)
    nonce = extract_nonce(data)
    ts = extract_event_timestamp(data)
    if ts:
        ok, msg = validate_event_timestamp(ts)
        if not ok:
            return {"error": msg}, 400
    if not event_id and not nonce:
        return {"error": "event_id or nonce is required for ingestion replay protection"}, 400
    action, meta = ingest_idempotency_guard(
        device_id=device.id,
        payload=data,
        event_id=event_id,
        nonce=nonce,
    )
    if action == "already_processed":
        return {"message": "Duplicate event ignored", **(meta or {}), "already_processed": True}, 200
    if action == "replay_rejected":
        raise IoTError("Replay request (nonce already used)", 409)
    if action == "idempotency_conflict":
        raise IoTError("Idempotency conflict (payload differs)", 409)
    try:
        payload = GPSMonitoringService.record_shock(data)
    except IoTError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Shock recorded", **payload}, 201


@iot_bp.route("/alerts", methods=["GET"])
def list_alerts():
    payload = ColdChainAlertService.list_alerts(
        device_id=request.args.get("device_id"),
        status=request.args.get("status"),
    )
    return payload


@iot_bp.route("/cold-chain/status", methods=["GET"])
def cold_chain_status():
    payload = ColdChainService.get_status(device_id=request.args.get("device_id"))
    return payload
