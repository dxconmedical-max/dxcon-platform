"""Device Gateway API routes — Phase 7.5."""

from __future__ import annotations

from flask import Blueprint

from app.services.device_gateway_service import (
    dashboard_payload,
    gateway_registry,
    astm_adapter,
    hl7_adapter,
    tcp_adapter,
    serial_adapter,
    usb_adapter,
    device_simulator,
    device_queue,
    retry_queue,
    device_audit,
    device_gateway_readiness_report,
)

device_gateway_bp = Blueprint("device_gateway_api", __name__, url_prefix="/api/v1/device-gateway")

@device_gateway_bp.route("/dashboard", methods=["GET"])
def device_gateway_dashboard_api():
    return dashboard_payload()

@device_gateway_bp.route("/registry", methods=["GET"])
def device_gateway_gateway_registry_api():
    return gateway_registry()

@device_gateway_bp.route("/astm", methods=["GET"])
def device_gateway_astm_adapter_api():
    return astm_adapter()

@device_gateway_bp.route("/hl7", methods=["GET"])
def device_gateway_hl7_adapter_api():
    return hl7_adapter()

@device_gateway_bp.route("/tcp", methods=["GET"])
def device_gateway_tcp_adapter_api():
    return tcp_adapter()

@device_gateway_bp.route("/serial", methods=["GET"])
def device_gateway_serial_adapter_api():
    return serial_adapter()

@device_gateway_bp.route("/usb", methods=["GET"])
def device_gateway_usb_adapter_api():
    return usb_adapter()

@device_gateway_bp.route("/simulator", methods=["GET"])
def device_gateway_device_simulator_api():
    return device_simulator()

@device_gateway_bp.route("/device-queue", methods=["GET"])
def device_gateway_device_queue_api():
    return device_queue()

@device_gateway_bp.route("/retry-queue", methods=["GET"])
def device_gateway_retry_queue_api():
    return retry_queue()

@device_gateway_bp.route("/audit", methods=["GET"])
def device_gateway_device_audit_api():
    return device_audit()

@device_gateway_bp.route("/readiness", methods=["GET"])
def device_gateway_readiness_api():
    return device_gateway_readiness_report()
