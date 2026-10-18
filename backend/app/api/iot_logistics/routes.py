"""IoT Cold Chain Logistics API routes — Phase 4 Sprint 4.3."""

from __future__ import annotations

from flask import Blueprint, request

from app.services.iot_logistics_service import (
    IoTLogisticsError,
    cold_chain_status,
    dashboard_payload,
    detect_temperature_breach,
    device_health,
    ingest_device_event,
    list_adapters,
    list_chain_of_custody,
    list_cold_boxes,
    list_devices,
    list_offline_buffer,
    list_sensor_alerts,
    route_timeline,
    sync_offline_buffer,
)

from app.core.authenticated_identity import require_authenticated_user
from app.core.iot_device_auth import (
    authenticate_iot_device,
    extract_event_timestamp,
    validate_device_identity_and_bind_payload,
)

iot_logistics_bp = Blueprint("iot_logistics_api", __name__, url_prefix="/api/v1/iot-logistics")


def _actor() -> str | None:
    from app.core.audit_actor import resolve_human_audit_actor

    return resolve_human_audit_actor(unauthenticated_fallback="") or None


@iot_logistics_bp.route("/dashboard", methods=["GET"])
@require_authenticated_user
def iot_logistics_dashboard_api():
    return dashboard_payload()


@iot_logistics_bp.route("/devices", methods=["GET"])
@require_authenticated_user
def iot_logistics_devices_api():
    return list_devices()


@iot_logistics_bp.route("/cold-boxes", methods=["GET"])
@require_authenticated_user
def iot_logistics_cold_boxes_api():
    return list_cold_boxes()


@iot_logistics_bp.route("/adapters", methods=["GET"])
@require_authenticated_user
def iot_logistics_adapters_api():
    return list_adapters()


@iot_logistics_bp.route("/alerts", methods=["GET"])
@require_authenticated_user
def iot_logistics_alerts_api():
    return list_sensor_alerts(
        device_id=request.args.get("device_id"),
        status=request.args.get("status"),
    )


@iot_logistics_bp.route("/chain-of-custody", methods=["GET"])
@require_authenticated_user
def iot_logistics_chain_api():
    return list_chain_of_custody(
        device_id=request.args.get("device_id"),
        limit=int(request.args.get("limit", 50)),
    )


@iot_logistics_bp.route("/timeline/<device_id>", methods=["GET"])
def iot_logistics_timeline_api(device_id):
    auth = authenticate_iot_device()
    if isinstance(auth, tuple):
        return auth
    if str(device_id) != str(auth.device.id):
        return {"error": "device_id mismatch"}, 403
    limit = int(request.args.get("limit", 50))
    return route_timeline(device_id, limit=limit)


@iot_logistics_bp.route("/temperature-breach", methods=["POST"])
def iot_logistics_breach_api():
    data = request.get_json(silent=True) or {}
    auth = authenticate_iot_device()
    if isinstance(auth, tuple):
        return auth
    data, err = validate_device_identity_and_bind_payload(device=auth.device, payload=data)
    if err is not None:
        return err
    # Also override/ensure selectors can't be used to probe other devices.
    return detect_temperature_breach(data)


@iot_logistics_bp.route("/offline-buffer", methods=["GET"])
@require_authenticated_user
def iot_logistics_offline_buffer_api():
    return list_offline_buffer(
        device_id=request.args.get("device_id"),
        status=request.args.get("status", "PENDING"),
    )


@iot_logistics_bp.route("/offline-buffer/sync", methods=["POST"])
def iot_logistics_offline_sync_api():
    data = request.get_json(silent=True) or {}
    auth = authenticate_iot_device()
    if isinstance(auth, tuple):
        return auth
    # Device must sync only its own offline buffer.
    return sync_offline_buffer(device_id=auth.device.id, actor=auth.device_actor)


@iot_logistics_bp.route("/device-health/<device_id>", methods=["GET"])
def iot_logistics_health_api(device_id):
    auth = authenticate_iot_device()
    if isinstance(auth, tuple):
        return auth
    if str(device_id) != str(auth.device.id):
        return {"error": "device_id mismatch"}, 403
    try:
        return device_health(device_id)
    except IoTLogisticsError as exc:
        return {"error": exc.message}, exc.status_code


@iot_logistics_bp.route("/cold-chain/status", methods=["GET"])
def iot_logistics_status_api():
    auth = authenticate_iot_device()
    if isinstance(auth, tuple):
        return auth
    requested = request.args.get("device_id")
    if requested and str(requested) != str(auth.device.id):
        return {"error": "device_id mismatch"}, 403
    return cold_chain_status(device_id=auth.device.id)


@iot_logistics_bp.route("/ingest", methods=["POST"])
def iot_logistics_ingest_api():
    data = request.get_json(silent=True) or {}
    auth = authenticate_iot_device()
    if isinstance(auth, tuple):
        return auth
    adapter_type = data.get("adapter_type") or request.headers.get("X-IoT-Adapter", "GENERIC")
    payload = data.get("payload") or data
    payload, err = validate_device_identity_and_bind_payload(device=auth.device, payload=payload)
    if err is not None:
        return err
    try:
        return ingest_device_event(
            adapter_type,
            payload,
            actor=auth.device_actor,
            offline=bool(data.get("offline") or payload.get("offline")),
            authenticated_device_id=auth.device.id,
            event_id_from_payload=payload.get("event_id") or payload.get("device_event_id"),
        )
    except IoTLogisticsError as exc:
        return {"error": exc.message}, exc.status_code
