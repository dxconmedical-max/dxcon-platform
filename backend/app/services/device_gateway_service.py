"""Device Gateway business logic for Phase 7.5."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.integration_platform import IntegrationJob
from app.models.iot_device import IoTDevice
from app.services.reporting_service import _safe

DEVICE_GATEWAY_ROLES = ("SUPER_ADMIN", "ADMIN")

FEATURES = (
    "Gateway Registry",
    "ASTM Adapter",
    "HL7 Adapter",
    "TCP Adapter",
    "Serial Adapter",
    "USB Adapter",
    "Simulator",
    "Device Queue",
    "Retry Queue",
    "Device Audit",
)

ADAPTERS = (
    {"id": "astm", "name": "ASTM Adapter", "protocol": "ASTM E1381", "status": "SCAFFOLD"},
    {"id": "hl7", "name": "HL7 Adapter", "protocol": "HL7 v2.x", "status": "READY", "route": "/api/v1/standards/hl7"},
    {"id": "tcp", "name": "TCP Adapter", "protocol": "TCP/IP", "status": "READY", "route": "/api/v1/iot/devices"},
    {"id": "serial", "name": "Serial Adapter", "protocol": "RS-232", "status": "SCAFFOLD"},
    {"id": "usb", "name": "USB Adapter", "protocol": "USB-HID", "status": "SCAFFOLD"},
)


def ensure_device_gateway() -> dict[str, Any]:
    return {"ready": True}


def gateway_registry() -> dict[str, Any]:
    ensure_device_gateway()
    devices = _safe(lambda: IoTDevice.query.count(), 0)
    return {"report": "gateway_registry", "adapters": list(ADAPTERS), "iot_devices": devices}


def astm_adapter() -> dict[str, Any]:
    return {"report": "astm_adapter", **ADAPTERS[0], "note": "ASTM parser scaffold for instrument ingest"}


def hl7_adapter() -> dict[str, Any]:
    return {"report": "hl7_adapter", **ADAPTERS[1]}


def tcp_adapter() -> dict[str, Any]:
    return {"report": "tcp_adapter", **ADAPTERS[2]}


def serial_adapter() -> dict[str, Any]:
    return {"report": "serial_adapter", **ADAPTERS[3]}


def usb_adapter() -> dict[str, Any]:
    return {"report": "usb_adapter", **ADAPTERS[4]}


def device_simulator() -> dict[str, Any]:
    return {"report": "device_simulator", "status": "READY", "endpoint": "/api/v1/iot-logistics/sandbox"}


def device_queue() -> dict[str, Any]:
    pending = _safe(lambda: IntegrationJob.query.filter_by(status="PENDING").count(), 0)
    return {"report": "device_queue", "pending_jobs": pending}


def retry_queue() -> dict[str, Any]:
    failed = _safe(lambda: IntegrationJob.query.filter_by(status="FAILED").count(), 0)
    return {"report": "retry_queue", "failed_jobs": failed}


def device_audit() -> dict[str, Any]:
    return {"report": "device_audit", "audit_route": "/api/v1/integration-hub/audit", "status": "READY"}


def dashboard_payload() -> dict[str, Any]:
    reg = gateway_registry()
    return {
        "platform": "Device Gateway",
        "phase": "7.5",
        "sprint": "Device Gateway",
        "status": "OK",
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {"adapters": len(ADAPTERS), "iot_devices": reg.get("iot_devices", 0)},
        "features": list(FEATURES),
    }


def device_gateway_readiness_report() -> dict[str, Any]:
    d = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "7.5",
        "platform": d["platform"],
        "status": d["status"],
        "summary": d["summary"],
        "features": list(FEATURES),
        "sections": {
            "gateway_registry": gateway_registry(),
            "astm_adapter": astm_adapter(),
            "hl7_adapter": hl7_adapter(),
            "tcp_adapter": tcp_adapter(),
            "serial_adapter": serial_adapter(),
            "usb_adapter": usb_adapter(),
            "device_simulator": device_simulator(),
            "device_queue": device_queue(),
            "retry_queue": retry_queue(),
            "device_audit": device_audit(),
        },
        "legacy_routes": ["/iot-logistics", "/api/v1/integration-hub", "/api/v1/standards/hl7"],
        "architecture_doc": "docs/architecture/DEVICE_GATEWAY_ARCHITECTURE.md",
    }
