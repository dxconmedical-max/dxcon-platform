"""IoT Cold Chain Logistics API routes — Phase 4 Sprint 4.3."""

from __future__ import annotations

from flask import Blueprint, request, session

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

iot_logistics_bp = Blueprint("iot_logistics_api", __name__, url_prefix="/api/v1/iot-logistics")


def _actor() -> str | None:
    return session.get("email")


@iot_logistics_bp.route("/dashboard", methods=["GET"])
def iot_logistics_dashboard_api():
    return dashboard_payload()


@iot_logistics_bp.route("/devices", methods=["GET"])
def iot_logistics_devices_api():
    return list_devices()


@iot_logistics_bp.route("/cold-boxes", methods=["GET"])
def iot_logistics_cold_boxes_api():
    return list_cold_boxes()


@iot_logistics_bp.route("/adapters", methods=["GET"])
def iot_logistics_adapters_api():
    return list_adapters()


@iot_logistics_bp.route("/alerts", methods=["GET"])
def iot_logistics_alerts_api():
    return list_sensor_alerts(
        device_id=request.args.get("device_id"),
        status=request.args.get("status"),
    )


@iot_logistics_bp.route("/chain-of-custody", methods=["GET"])
def iot_logistics_chain_api():
    return list_chain_of_custody(
        device_id=request.args.get("device_id"),
        limit=int(request.args.get("limit", 50)),
    )


@iot_logistics_bp.route("/timeline/<device_id>", methods=["GET"])
def iot_logistics_timeline_api(device_id):
    limit = int(request.args.get("limit", 50))
    return route_timeline(device_id, limit=limit)


@iot_logistics_bp.route("/temperature-breach", methods=["POST"])
def iot_logistics_breach_api():
    data = request.get_json(silent=True) or {}
    return detect_temperature_breach(data)


@iot_logistics_bp.route("/offline-buffer", methods=["GET"])
def iot_logistics_offline_buffer_api():
    return list_offline_buffer(
        device_id=request.args.get("device_id"),
        status=request.args.get("status", "PENDING"),
    )


@iot_logistics_bp.route("/offline-buffer/sync", methods=["POST"])
def iot_logistics_offline_sync_api():
    data = request.get_json(silent=True) or {}
    return sync_offline_buffer(device_id=data.get("device_id"), actor=_actor())


@iot_logistics_bp.route("/device-health/<device_id>", methods=["GET"])
def iot_logistics_health_api(device_id):
    try:
        return device_health(device_id)
    except IoTLogisticsError as exc:
        return {"error": exc.message}, exc.status_code


@iot_logistics_bp.route("/cold-chain/status", methods=["GET"])
def iot_logistics_status_api():
    return cold_chain_status(device_id=request.args.get("device_id"))


@iot_logistics_bp.route("/ingest", methods=["POST"])
def iot_logistics_ingest_api():
    data = request.get_json(silent=True) or {}
    adapter_type = data.get("adapter_type") or request.headers.get("X-IoT-Adapter", "GENERIC")
    payload = data.get("payload") or data
    try:
        return ingest_device_event(
            adapter_type,
            payload,
            actor=_actor(),
            offline=bool(data.get("offline") or payload.get("offline")),
        )
    except IoTLogisticsError as exc:
        return {"error": exc.message}, exc.status_code
