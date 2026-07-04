"""IoT Cold Chain Logistics web routes — Phase 4 Sprint 4.3."""

from __future__ import annotations

import json

from flask import Blueprint, request, session

from app.services.iot_logistics_service import IoTLogisticsError, LOGISTICS_ROLES, ingest_device_event
from app.utils.auth import role_required
from app.web.iot_logistics_lib import (
    build_adapters_body,
    build_alerts_body,
    build_chain_of_custody_body,
    build_cold_boxes_body,
    build_dashboard_body,
    build_device_health_body,
    build_devices_body,
    build_ingest_form_body,
    build_offline_buffer_body,
    build_timeline_body,
    render_logistics_page,
)

iot_logistics_web_bp = Blueprint("iot_logistics_web", __name__)


def _actor() -> str | None:
    return session.get("email")


@iot_logistics_web_bp.route("/iot-logistics")
@role_required(*LOGISTICS_ROLES)
def iot_logistics_dashboard():
    return render_logistics_page("IoT Logistics Dashboard", build_dashboard_body())


@iot_logistics_web_bp.route("/iot-logistics/devices")
@role_required(*LOGISTICS_ROLES)
def iot_logistics_devices():
    return render_logistics_page("IoT Devices", build_devices_body())


@iot_logistics_web_bp.route("/iot-logistics/cold-boxes")
@role_required(*LOGISTICS_ROLES)
def iot_logistics_cold_boxes():
    return render_logistics_page("Cold Boxes", build_cold_boxes_body())


@iot_logistics_web_bp.route("/iot-logistics/adapters")
@role_required(*LOGISTICS_ROLES)
def iot_logistics_adapters():
    return render_logistics_page("Device Adapters", build_adapters_body())


@iot_logistics_web_bp.route("/iot-logistics/alerts")
@role_required(*LOGISTICS_ROLES)
def iot_logistics_alerts():
    return render_logistics_page("Sensor Alerts", build_alerts_body())


@iot_logistics_web_bp.route("/iot-logistics/timeline")
@role_required(*LOGISTICS_ROLES)
def iot_logistics_timeline():
    device_id = request.args.get("device_id", "").strip()
    return render_logistics_page("Route Timeline", build_timeline_body(device_id=device_id))


@iot_logistics_web_bp.route("/iot-logistics/chain-of-custody")
@role_required(*LOGISTICS_ROLES)
def iot_logistics_chain_of_custody():
    return render_logistics_page("Chain of Custody", build_chain_of_custody_body())


@iot_logistics_web_bp.route("/iot-logistics/offline-buffer")
@role_required(*LOGISTICS_ROLES)
def iot_logistics_offline_buffer():
    return render_logistics_page("Offline Buffer", build_offline_buffer_body())


@iot_logistics_web_bp.route("/iot-logistics/device-health")
@role_required(*LOGISTICS_ROLES)
def iot_logistics_device_health():
    device_id = request.args.get("device_id", "").strip()
    return render_logistics_page("Device Health", build_device_health_body(device_id=device_id))


@iot_logistics_web_bp.route("/iot-logistics/ingest", methods=["GET", "POST"])
@role_required(*LOGISTICS_ROLES)
def iot_logistics_ingest():
    if request.method == "GET":
        return render_logistics_page("Device Ingestion", build_ingest_form_body())
    try:
        payload = json.loads(request.form.get("payload", "").strip())
        result = ingest_device_event(
            request.form.get("adapter_type", "GENERIC"),
            payload,
            actor=_actor(),
            offline=bool(payload.get("offline")),
        )
        return render_logistics_page("Device Ingestion", build_ingest_form_body(result=result))
    except json.JSONDecodeError:
        return render_logistics_page("Device Ingestion", build_ingest_form_body(error="Invalid JSON payload."))
    except IoTLogisticsError as exc:
        return render_logistics_page("Device Ingestion", build_ingest_form_body(error=exc.message))
