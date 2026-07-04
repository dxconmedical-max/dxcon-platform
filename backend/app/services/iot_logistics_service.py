"""IoT Cold Chain Logistics business logic for Phase 4 Sprint 4.3."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import Any

from app.core.statuses import COLD_CHAIN_ALERT_TEMP_HIGH, COLD_CHAIN_ALERT_TEMP_LOW
from app.extensions.db import db
from app.iot.adapter_manager import IoTAdapterManager
from app.models.battery_event import BatteryEvent
from app.models.cold_box_device import ColdBoxDevice
from app.models.cold_chain_alert import ColdChainAlert
from app.models.gps_reading import GPSReading
from app.models.iot_device import IoTDevice
from app.models.iot_offline_event_buffer import IoTOfflineEventBuffer
from app.models.logistics_tracking import ChainOfCustodyEvent
from app.models.shock_event import ShockEvent
from app.models.temperature_reading import TemperatureReading
from app.services.iot_cold_chain_service import (
    ColdChainAlertService,
    ColdChainService,
    GPSMonitoringService,
    IoTDeviceService,
    IoTError,
    TemperatureMonitoringService,
)

LOGISTICS_ROLES = ("SUPER_ADMIN", "ADMIN", "COLLECTOR")

FEATURES = (
    "IoT Device Registry",
    "Cold Box Registry",
    "Temperature Event",
    "GPS Event",
    "Shock Event",
    "Chain of Custody",
    "Sensor Alert",
    "Route Timeline",
    "Temperature Breach Detection",
    "Offline Device Event Buffer",
    "Logistics IoT Dashboard",
    "Device Health",
    "API for Device Ingestion",
    "Verification Report",
)


class IoTLogisticsError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def ensure_logistics() -> dict[str, Any]:
    IoTAdapterManager.initialize()
    devices = IoTDeviceService.list_devices()
    if devices["count"] == 0:
        IoTDeviceService.register_device(
            {
                "device_code": "IOT-LOG-001",
                "box_code": "BOX-LOG-001",
                "device_type": "COLD_BOX",
                "serial_number": "SN-LOG-001",
            }
        )
    return {"ready": True}


def dashboard_payload() -> dict[str, Any]:
    ensure_logistics()
    devices = IoTDeviceService.list_devices()
    boxes = list_cold_boxes()
    alerts = ColdChainAlertService.list_alerts(status="OPEN")
    buffer = list_offline_buffer()
    status = ColdChainService.get_status()
    return {
        "platform": "IoT Cold Chain Logistics",
        "phase": "4.3",
        "sprint": "IoT Cold Chain Logistics",
        "status": "OK",
        "summary": {
            "devices": devices["count"],
            "cold_boxes": boxes["count"],
            "open_alerts": alerts["count"],
            "offline_buffered": buffer["pending"],
            "devices_in_range": status.get("summary", {}).get("devices_in_range", 0),
            "adapters": IoTAdapterManager.list_adapters()["count"],
        },
        "features": list(FEATURES),
    }


def list_devices() -> dict[str, Any]:
    ensure_logistics()
    return IoTDeviceService.list_devices()


def list_cold_boxes() -> dict[str, Any]:
    ensure_logistics()
    rows = ColdBoxDevice.query.order_by(ColdBoxDevice.created_at.desc()).all()
    return {"count": len(rows), "cold_boxes": [row.to_dict() for row in rows]}


def list_adapters() -> dict[str, Any]:
    ensure_logistics()
    return IoTAdapterManager.list_adapters()


def list_sensor_alerts(*, device_id: str | None = None, status: str | None = None) -> dict[str, Any]:
    ensure_logistics()
    return ColdChainAlertService.list_alerts(device_id=device_id, status=status)


def _record_chain_of_custody(
    device_id: str,
    event_type: str,
    *,
    actor: str | None = None,
    location: str | None = None,
    detail: dict | None = None,
) -> dict[str, Any]:
    row = ChainOfCustodyEvent(
        event_code=f"COC-{uuid.uuid4().hex[:10].upper()}",
        event_type=event_type,
        reference_type="IoTDevice",
        reference_id=device_id,
        actor=actor or "SYSTEM",
        location=location,
        metadata_json=json.dumps(detail or {}),
    )
    db.session.add(row)
    db.session.flush()
    return row.to_dict()


def _process_normalized_event(normalized: dict[str, Any], *, actor: str | None = None) -> dict[str, Any]:
    event_type = normalized.get("event_type", "").upper()
    data = dict(normalized.get("data") or {})
    device_id = normalized.get("device_id") or data.get("device_id")
    if not device_id:
        raise IoTLogisticsError("device_id is required", 400)
    data["device_id"] = device_id

    if event_type in {"TEMPERATURE", "TEMP"}:
        result = TemperatureMonitoringService.record_temperature(
            {"device_id": device_id, "celsius": data.get("celsius")}
        )
        custody = _record_chain_of_custody(
            device_id,
            "TEMPERATURE_RECORDED",
            actor=actor,
            detail={"celsius": data.get("celsius"), "reading_id": result["reading"]["id"]},
        )
        db.session.commit()
        return {"event_type": event_type, "result": result, "chain_of_custody": custody}

    if event_type == "GPS":
        result = GPSMonitoringService.record_gps(
            {
                "device_id": device_id,
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
            }
        )
        reading = result["reading"]
        custody = _record_chain_of_custody(
            device_id,
            "GPS_RECORDED",
            actor=actor,
            location=f"{reading.get('latitude')},{reading.get('longitude')}",
            detail=reading,
        )
        db.session.commit()
        return {"event_type": event_type, "result": result, "chain_of_custody": custody}

    if event_type == "SHOCK":
        result = GPSMonitoringService.record_shock({"device_id": device_id, "g_force": data.get("g_force")})
        custody = _record_chain_of_custody(
            device_id,
            "SHOCK_DETECTED",
            actor=actor,
            detail={"g_force": data.get("g_force"), "event_id": result["event"]["id"]},
        )
        db.session.commit()
        return {"event_type": event_type, "result": result, "chain_of_custody": custody}

    if event_type in {"BATTERY", "TELEMETRY"}:
        results = {}
        if data.get("celsius") is not None:
            results["temperature"] = TemperatureMonitoringService.record_temperature(
                {"device_id": device_id, "celsius": data.get("celsius")}
            )
        if data.get("latitude") is not None and data.get("longitude") is not None:
            results["gps"] = GPSMonitoringService.record_gps(
                {
                    "device_id": device_id,
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude"),
                }
            )
        if data.get("g_force") is not None:
            results["shock"] = GPSMonitoringService.record_shock(
                {"device_id": device_id, "g_force": data.get("g_force")}
            )
        if data.get("battery_percent") is not None:
            results["battery"] = GPSMonitoringService.record_battery(
                {"device_id": device_id, "battery_percent": data.get("battery_percent")}
            )
        if not results:
            raise IoTLogisticsError(f"Unsupported event_type: {event_type}", 400)
        custody = _record_chain_of_custody(device_id, "TELEMETRY_INGESTED", actor=actor, detail={"keys": list(results)})
        db.session.commit()
        return {"event_type": event_type, "results": results, "chain_of_custody": custody}

    raise IoTLogisticsError(f"Unsupported event_type: {event_type}", 400)


def buffer_offline_event(
    adapter_type: str,
    payload: dict[str, Any],
    *,
    actor: str | None = None,
) -> dict[str, Any]:
    ensure_logistics()
    normalized = IoTAdapterManager.normalize(adapter_type, payload)
    device_id = normalized.get("device_id")
    if not device_id:
        raise IoTLogisticsError("device_id is required for offline buffer", 400)
    row = IoTOfflineEventBuffer(
        device_id=device_id,
        adapter_type=(adapter_type or "GENERIC").upper(),
        event_type=normalized.get("event_type", "UNKNOWN"),
        payload_json=json.dumps(payload),
        status="PENDING",
    )
    db.session.add(row)
    db.session.flush()
    _record_chain_of_custody(
        device_id,
        "OFFLINE_BUFFERED",
        actor=actor,
        detail={"buffer_id": row.id, "event_type": row.event_type},
    )
    db.session.commit()
    return {"buffered": True, "event": row.to_dict()}


def list_offline_buffer(*, device_id: str | None = None, status: str = "PENDING") -> dict[str, Any]:
    ensure_logistics()
    query = IoTOfflineEventBuffer.query
    if device_id:
        query = query.filter_by(device_id=device_id)
    if status:
        query = query.filter_by(status=status)
    rows = query.order_by(IoTOfflineEventBuffer.buffered_at.asc()).all()
    pending = IoTOfflineEventBuffer.query.filter_by(status="PENDING").count()
    return {"count": len(rows), "pending": pending, "events": [row.to_dict() for row in rows]}


def sync_offline_buffer(*, device_id: str | None = None, actor: str | None = None) -> dict[str, Any]:
    ensure_logistics()
    query = IoTOfflineEventBuffer.query.filter_by(status="PENDING")
    if device_id:
        query = query.filter_by(device_id=device_id)
    rows = query.order_by(IoTOfflineEventBuffer.buffered_at.asc()).all()
    synced = []
    for row in rows:
        payload = json.loads(row.payload_json or "{}")
        normalized = IoTAdapterManager.normalize(row.adapter_type, payload)
        result = _process_normalized_event(normalized, actor=actor)
        row.status = "SYNCED"
        row.synced_at = datetime.utcnow()
        synced.append({"buffer_id": row.id, "result": result})
    db.session.commit()
    return {"synced_count": len(synced), "events": synced}


def ingest_device_event(
    adapter_type: str,
    payload: dict[str, Any],
    *,
    actor: str | None = None,
    offline: bool = False,
) -> dict[str, Any]:
    ensure_logistics()
    if offline or payload.get("offline"):
        return buffer_offline_event(adapter_type, payload, actor=actor)
    try:
        normalized = IoTAdapterManager.normalize(adapter_type, payload)
        result = _process_normalized_event(normalized, actor=actor)
        return {"adapter_type": (adapter_type or "GENERIC").upper(), "ingested": True, **result}
    except (IoTError, ValueError, KeyError) as exc:
        message = getattr(exc, "message", None) or str(exc)
        raise IoTLogisticsError(message, getattr(exc, "status_code", 400)) from exc


def detect_temperature_breach(data: dict[str, Any]) -> dict[str, Any]:
    ensure_logistics()
    device_id = data.get("device_id")
    celsius = data.get("celsius")
    if not device_id:
        raise IoTLogisticsError("device_id is required", 400)
    cold_box = ColdBoxDevice.query.filter_by(device_id=device_id).first()
    if celsius is None:
        latest = (
            TemperatureReading.query.filter_by(device_id=device_id)
            .order_by(TemperatureReading.recorded_at.desc())
            .first()
        )
        celsius = latest.celsius if latest else None
    if celsius is None or not cold_box:
        return {"breach": False, "reason": "missing_temperature_or_cold_box"}
    breach = celsius > cold_box.max_temp_c or celsius < cold_box.min_temp_c
    alert_type = None
    if celsius > cold_box.max_temp_c:
        alert_type = COLD_CHAIN_ALERT_TEMP_HIGH
    elif celsius < cold_box.min_temp_c:
        alert_type = COLD_CHAIN_ALERT_TEMP_LOW
    return {
        "device_id": device_id,
        "celsius": celsius,
        "min_temp_c": cold_box.min_temp_c,
        "max_temp_c": cold_box.max_temp_c,
        "breach": breach,
        "alert_type": alert_type,
        "in_range": not breach,
    }


def route_timeline(device_id: str, *, limit: int = 50) -> dict[str, Any]:
    ensure_logistics()
    if not device_id:
        raise IoTLogisticsError("device_id is required", 400)
    events: list[dict[str, Any]] = []

    for row in TemperatureReading.query.filter_by(device_id=device_id).all():
        events.append(
            {
                "kind": "TEMPERATURE",
                "timestamp": row.recorded_at.isoformat() if row.recorded_at else None,
                "payload": row.to_dict(),
            }
        )
    for row in GPSReading.query.filter_by(device_id=device_id).all():
        events.append(
            {
                "kind": "GPS",
                "timestamp": row.recorded_at.isoformat() if row.recorded_at else None,
                "payload": row.to_dict(),
            }
        )
    for row in ShockEvent.query.filter_by(device_id=device_id).all():
        events.append(
            {
                "kind": "SHOCK",
                "timestamp": row.recorded_at.isoformat() if row.recorded_at else None,
                "payload": row.to_dict(),
            }
        )
    for row in ChainOfCustodyEvent.query.filter_by(reference_type="IoTDevice", reference_id=device_id).all():
        events.append(
            {
                "kind": "CHAIN_OF_CUSTODY",
                "timestamp": row.created_at.isoformat() if row.created_at else None,
                "payload": row.to_dict(),
            }
        )

    events.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
    trimmed = events[: max(int(limit or 50), 1)]
    return {"device_id": device_id, "count": len(trimmed), "timeline": trimmed}


def list_chain_of_custody(*, device_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    ensure_logistics()
    query = ChainOfCustodyEvent.query.filter_by(reference_type="IoTDevice")
    if device_id:
        query = query.filter_by(reference_id=device_id)
    rows = query.order_by(ChainOfCustodyEvent.created_at.desc()).limit(min(limit, 200)).all()
    return {"count": len(rows), "events": [row.to_dict() for row in rows]}


def device_health(device_id: str) -> dict[str, Any]:
    ensure_logistics()
    device = IoTDevice.query.filter_by(id=device_id).first()
    if not device:
        raise IoTLogisticsError("IoT device not found", 404)
    latest_battery = (
        BatteryEvent.query.filter_by(device_id=device_id)
        .order_by(BatteryEvent.recorded_at.desc())
        .first()
    )
    latest_temp = (
        TemperatureReading.query.filter_by(device_id=device_id)
        .order_by(TemperatureReading.recorded_at.desc())
        .first()
    )
    open_alerts = ColdChainAlert.query.filter_by(device_id=device_id, status="OPEN").count()
    pending_buffer = IoTOfflineEventBuffer.query.filter_by(device_id=device_id, status="PENDING").count()
    online = False
    if device.last_seen_at:
        online = device.last_seen_at >= datetime.utcnow() - timedelta(minutes=15)
    battery_percent = latest_battery.battery_percent if latest_battery else None
    health_score = 100
    if not online:
        health_score -= 30
    if open_alerts:
        health_score -= min(open_alerts * 10, 40)
    if battery_percent is not None and battery_percent <= 20:
        health_score -= 20
    if pending_buffer:
        health_score -= min(pending_buffer * 5, 15)
    health_score = max(health_score, 0)
    return {
        "device": device.to_dict(),
        "connectivity": "ONLINE" if online else "OFFLINE",
        "battery_percent": battery_percent,
        "latest_temperature": latest_temp.to_dict() if latest_temp else None,
        "open_alerts": open_alerts,
        "pending_offline_events": pending_buffer,
        "health_score": health_score,
        "healthy": health_score >= 70,
    }


def cold_chain_status(device_id: str | None = None) -> dict[str, Any]:
    ensure_logistics()
    return ColdChainService.get_status(device_id=device_id)
