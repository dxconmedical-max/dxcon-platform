"""Device Gateway web routes — Phase 7.5."""

from __future__ import annotations

from flask import Blueprint

from app.services.device_gateway_service import DEVICE_GATEWAY_ROLES
from app.utils.auth import role_required
from app.web.device_gateway_lib import (
    build_dashboard_body,
    build_gateway_registry_body,
    build_astm_adapter_body,
    build_hl7_adapter_body,
    build_tcp_adapter_body,
    build_serial_adapter_body,
    build_usb_adapter_body,
    build_device_simulator_body,
    build_device_queue_body,
    build_retry_queue_body,
    build_device_audit_body,
    render_hub_page,
)

device_gateway_web_bp = Blueprint("device_gateway_web", __name__)

@device_gateway_web_bp.route("/device-gateway")
@role_required(*DEVICE_GATEWAY_ROLES)
def device_gateway_dashboard():
    return render_hub_page("Device Gateway", build_dashboard_body())
@device_gateway_web_bp.route("/device-gateway/registry")
@role_required(*DEVICE_GATEWAY_ROLES)
def device_gateway_gateway_registry():
    return render_hub_page("Gateway Registry", build_gateway_registry_body())
@device_gateway_web_bp.route("/device-gateway/astm")
@role_required(*DEVICE_GATEWAY_ROLES)
def device_gateway_astm_adapter():
    return render_hub_page("ASTM Adapter", build_astm_adapter_body())
@device_gateway_web_bp.route("/device-gateway/hl7")
@role_required(*DEVICE_GATEWAY_ROLES)
def device_gateway_hl7_adapter():
    return render_hub_page("HL7 Adapter", build_hl7_adapter_body())
@device_gateway_web_bp.route("/device-gateway/tcp")
@role_required(*DEVICE_GATEWAY_ROLES)
def device_gateway_tcp_adapter():
    return render_hub_page("TCP Adapter", build_tcp_adapter_body())
@device_gateway_web_bp.route("/device-gateway/serial")
@role_required(*DEVICE_GATEWAY_ROLES)
def device_gateway_serial_adapter():
    return render_hub_page("Serial Adapter", build_serial_adapter_body())
@device_gateway_web_bp.route("/device-gateway/usb")
@role_required(*DEVICE_GATEWAY_ROLES)
def device_gateway_usb_adapter():
    return render_hub_page("USB Adapter", build_usb_adapter_body())
@device_gateway_web_bp.route("/device-gateway/simulator")
@role_required(*DEVICE_GATEWAY_ROLES)
def device_gateway_device_simulator():
    return render_hub_page("Simulator", build_device_simulator_body())
@device_gateway_web_bp.route("/device-gateway/device-queue")
@role_required(*DEVICE_GATEWAY_ROLES)
def device_gateway_device_queue():
    return render_hub_page("Device Queue", build_device_queue_body())
@device_gateway_web_bp.route("/device-gateway/retry-queue")
@role_required(*DEVICE_GATEWAY_ROLES)
def device_gateway_retry_queue():
    return render_hub_page("Retry Queue", build_retry_queue_body())
@device_gateway_web_bp.route("/device-gateway/audit")
@role_required(*DEVICE_GATEWAY_ROLES)
def device_gateway_device_audit():
    return render_hub_page("Device Audit", build_device_audit_body())

