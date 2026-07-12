"""IoT Logistics Platform service layer."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func

from app.core.statuses import (
    EXCURSION_ACTIVE,
    EXCURSION_ACKNOWLEDGED,
    EXCURSION_DETECTED,
    EXCURSION_RESOLVED,
    EXCURSION_SAMPLE_HOLD,
    IOT_DEVICE_ACTIVE,
    IOT_DEVICE_PROVISIONING,
    IOT_DEVICE_TYPES,
    LOGISTICS_TRIP_ACTIVE,
    LOGISTICS_TRIP_CANCELLED,
    LOGISTICS_TRIP_COMPLETED,
    LOGISTICS_TRIP_PLANNED,
)
from app.extensions.db import db
from app.iot_platform.ingestion import IngestionError, ingest_telemetry, provision_device_credential
from app.models.iot_device import IoTDevice
from app.models.iot_platform import (
    IoTColdChainExcursion,
    IoTCanonicalReading,
    IoTDeviceAssignment,
    IoTPlatformAlert,
    IoTThresholdPolicy,
    LogisticsTransportTrip,
)
from app.models.logistics_route import RoutePlan, RouteStop
from app.models.logistics_tracking import ChainOfCustodyEvent
from app.models.transport_box import TransportBox


class IoTPlatformError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.utcnow()


def _trip_code() -> str:
    return f"TRIP-{_utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


def _device_public_dict(device: IoTDevice) -> dict[str, Any]:
    data = device.to_dict()
    for key in ("credential_hash", "credential_ref", "api_key"):
        data.pop(key, None)
    return data


def register_device(data: dict[str, Any], *, organization_id: str, actor: str | None = None) -> dict[str, Any]:
    device_type = data.get("device_type", "cold_chain_tracker")
    if device_type not in IOT_DEVICE_TYPES and device_type not in ("COLD_BOX",):
        raise IoTPlatformError(f"Unsupported device type: {device_type}")
    code = data.get("device_code") or f"IOT-{uuid.uuid4().hex[:8].upper()}"
    if IoTDevice.query.filter_by(device_code=code).first():
        raise IoTPlatformError("Device code already exists")
    device = IoTDevice(
        device_code=code,
        device_type=device_type,
        serial_number=data.get("serial_number"),
        status=data.get("status", IOT_DEVICE_PROVISIONING),
        partner_id=organization_id,
    )
    for attr in ("vendor", "model", "firmware_version", "connectivity_type", "organization_id",
                 "assigned_vehicle_id", "assigned_container_id", "certificate_reference"):
        if hasattr(device, attr) and data.get(attr.replace("organization_id", "organization_id")) is not None:
            setattr(device, attr, data.get(attr) if attr != "organization_id" else organization_id)
    if hasattr(device, "organization_id"):
        device.organization_id = organization_id
    db.session.add(device)
    db.session.flush()
    cred = provision_device_credential(device.id)
    return {"device": _device_public_dict(device), "provisioning": cred}


def list_devices(*, organization_id: str | None = None, status: str | None = None, page: int = 1, per_page: int = 25) -> dict:
    q = IoTDevice.query
    if organization_id and hasattr(IoTDevice, "organization_id"):
        q = q.filter(IoTDevice.organization_id == organization_id)
    elif organization_id:
        q = q.filter(IoTDevice.partner_id == organization_id)
    if status:
        q = q.filter(IoTDevice.status == status)
    total = q.count()
    rows = q.order_by(IoTDevice.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {"total": total, "page": page, "per_page": per_page, "devices": [_device_public_dict(r) for r in rows]}


def get_device(device_id: str, *, organization_id: str | None = None) -> dict:
    device = IoTDevice.query.get(device_id)
    if not device:
        raise IoTPlatformError("Device not found")
    if organization_id:
        org = getattr(device, "organization_id", None) or device.partner_id
        if org and org != organization_id:
            raise IoTPlatformError("Tenant isolation violation")
    return _device_public_dict(device)


def list_readings(
    *,
    organization_id: str,
    device_id: str | None = None,
    trip_id: str | None = None,
    page: int = 1,
    per_page: int = 50,
) -> dict:
    q = IoTCanonicalReading.query.filter_by(organization_id=organization_id)
    if device_id:
        q = q.filter_by(device_id=device_id)
    if trip_id:
        q = q.filter_by(trip_id=trip_id)
    total = q.count()
    rows = q.order_by(IoTCanonicalReading.recorded_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {"total": total, "readings": [r.to_dict() for r in rows]}


def create_threshold_policy(data: dict[str, Any], *, organization_id: str, actor: str) -> dict:
    code = data.get("policy_code") or f"POL-{uuid.uuid4().hex[:6].upper()}"
    policy = IoTThresholdPolicy(
        organization_id=organization_id,
        policy_code=code,
        name=data["name"],
        specimen_type=data.get("specimen_type"),
        container_type=data.get("container_type"),
        min_temperature_c=data.get("min_temperature_c"),
        max_temperature_c=data.get("max_temperature_c"),
        min_humidity_percent=data.get("min_humidity_percent"),
        max_humidity_percent=data.get("max_humidity_percent"),
        grace_duration_seconds=data.get("grace_duration_seconds", 300),
        approved_by=actor,
        approved_at=_utcnow(),
    )
    db.session.add(policy)
    db.session.flush()
    return policy.to_dict()


def evaluate_excursion(reading: IoTCanonicalReading, policy: IoTThresholdPolicy) -> IoTColdChainExcursion | None:
    breach = None
    if reading.temperature_c is not None:
        if policy.min_temperature_c is not None and reading.temperature_c < policy.min_temperature_c:
            breach = "temperature_low"
        if policy.max_temperature_c is not None and reading.temperature_c > policy.max_temperature_c:
            breach = "temperature_high"
    if not breach:
        return None
    excursion = IoTColdChainExcursion(
        organization_id=reading.organization_id,
        device_id=reading.device_id,
        trip_id=reading.trip_id,
        transport_container_id=reading.transport_container_id,
        policy_id=policy.id,
        excursion_type=breach,
        state=EXCURSION_DETECTED,
        correlation_id=reading.id,
    )
    db.session.add(excursion)
    _raise_alert(
        organization_id=reading.organization_id,
        alert_type="temperature_excursion",
        device_id=reading.device_id,
        trip_id=reading.trip_id,
        message=f"Temperature excursion detected: {breach}",
        dedupe_key=f"excursion:{reading.device_id}:{breach}",
    )
    return excursion


def _raise_alert(
    *,
    organization_id: str,
    alert_type: str,
    message: str,
    device_id: str | None = None,
    trip_id: str | None = None,
    dedupe_key: str | None = None,
    severity: str = "WARNING",
) -> IoTPlatformAlert | None:
    if dedupe_key:
        existing = IoTPlatformAlert.query.filter_by(dedupe_key=dedupe_key, status="OPEN").first()
        if existing:
            return None
    alert = IoTPlatformAlert(
        organization_id=organization_id,
        alert_type=alert_type,
        severity=severity,
        device_id=device_id,
        trip_id=trip_id,
        dedupe_key=dedupe_key,
        message=message,
        channel="in_app",
    )
    db.session.add(alert)
    return alert


def list_alerts(*, organization_id: str, status: str | None = None, page: int = 1, per_page: int = 25) -> dict:
    q = IoTPlatformAlert.query.filter_by(organization_id=organization_id)
    if status:
        q = q.filter_by(status=status)
    total = q.count()
    rows = q.order_by(IoTPlatformAlert.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {"total": total, "alerts": [r.to_dict() for r in rows]}


def list_excursions(*, organization_id: str, state: str | None = None) -> dict:
    q = IoTColdChainExcursion.query.filter_by(organization_id=organization_id)
    if state:
        q = q.filter_by(state=state)
    rows = q.order_by(IoTColdChainExcursion.detected_at.desc()).all()
    return {"count": len(rows), "excursions": [r.to_dict() for r in rows]}


def acknowledge_excursion(excursion_id: str, *, actor: str, organization_id: str) -> dict:
    row = IoTColdChainExcursion.query.get(excursion_id)
    if not row or row.organization_id != organization_id:
        raise IoTPlatformError("Excursion not found")
    row.state = EXCURSION_ACKNOWLEDGED
    row.acknowledged_by = actor
    row.acknowledged_at = _utcnow()
    return row.to_dict()


def hold_specimen_for_excursion(excursion_id: str, *, actor: str, organization_id: str) -> dict:
    row = IoTColdChainExcursion.query.get(excursion_id)
    if not row or row.organization_id != organization_id:
        raise IoTPlatformError("Excursion not found")
    row.state = EXCURSION_SAMPLE_HOLD
    row.specimen_hold = True
    row.acknowledged_by = actor
    row.acknowledged_at = _utcnow()
    return row.to_dict()


def create_trip(data: dict[str, Any], *, organization_id: str) -> dict:
    trip = LogisticsTransportTrip(
        organization_id=organization_id,
        trip_code=data.get("trip_code") or _trip_code(),
        driver_profile_id=data.get("driver_profile_id"),
        vehicle_id=data.get("vehicle_id"),
        container_id=data.get("container_id"),
        route_plan_id=data.get("route_plan_id"),
        status=LOGISTICS_TRIP_PLANNED,
        eta_provider=data.get("eta_provider", "test"),
        correlation_id=data.get("correlation_id") or uuid.uuid4().hex,
    )
    db.session.add(trip)
    db.session.flush()
    return trip.to_dict()


def list_trips(*, organization_id: str, status: str | None = None, page: int = 1, per_page: int = 25) -> dict:
    q = LogisticsTransportTrip.query.filter_by(organization_id=organization_id)
    if status:
        q = q.filter_by(status=status)
    total = q.count()
    rows = q.order_by(LogisticsTransportTrip.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {"total": total, "trips": [r.to_dict() for r in rows]}


def get_trip(trip_id: str, *, organization_id: str) -> dict:
    trip = LogisticsTransportTrip.query.get(trip_id)
    if not trip or trip.organization_id != organization_id:
        raise IoTPlatformError("Trip not found")
    return trip.to_dict()


def transition_trip(trip_id: str, *, action: str, organization_id: str, actor: str | None = None) -> dict:
    trip = LogisticsTransportTrip.query.get(trip_id)
    if not trip or trip.organization_id != organization_id:
        raise IoTPlatformError("Trip not found")
    now = _utcnow()
    if action == "start":
        trip.status = LOGISTICS_TRIP_ACTIVE
        trip.started_at = now
        _append_custody("transport_started", trip=trip, actor=actor)
    elif action == "complete":
        trip.status = LOGISTICS_TRIP_COMPLETED
        trip.completed_at = now
        _append_custody("handover_signed", trip=trip, actor=actor)
    elif action == "cancel":
        trip.status = LOGISTICS_TRIP_CANCELLED
        trip.cancelled_at = now
    else:
        raise IoTPlatformError(f"Unknown trip action: {action}")
    return trip.to_dict()


def trip_locations(trip_id: str, *, organization_id: str) -> dict:
    trip = LogisticsTransportTrip.query.get(trip_id)
    if not trip or trip.organization_id != organization_id:
        raise IoTPlatformError("Trip not found")
    readings = (
        IoTCanonicalReading.query.filter_by(organization_id=organization_id, trip_id=trip_id)
        .filter(IoTCanonicalReading.latitude.isnot(None))
        .order_by(IoTCanonicalReading.recorded_at.asc())
        .all()
    )
    return {"trip_id": trip_id, "locations": [r.to_dict() for r in readings]}


def trip_timeline(trip_id: str, *, organization_id: str) -> dict:
    events = ChainOfCustodyEvent.query.filter(
        ChainOfCustodyEvent.reference_type == "trip",
        ChainOfCustodyEvent.reference_id == trip_id,
    ).order_by(ChainOfCustodyEvent.created_at.asc()).all()
    return {"trip_id": trip_id, "events": [e.to_dict() for e in events]}


def _append_custody(event_type: str, *, trip: LogisticsTransportTrip, actor: str | None) -> None:
    db.session.add(
        ChainOfCustodyEvent(
            event_code=f"COC-{uuid.uuid4().hex[:10].upper()}",
            event_type=event_type,
            reference_type="trip",
            reference_id=trip.id,
            actor=actor or "SYSTEM",
            location=f"{trip.latest_latitude},{trip.latest_longitude}" if trip.latest_latitude else None,
            metadata_json=json.dumps({"trip_code": trip.trip_code, "organization_id": trip.organization_id}),
        )
    )


def append_custody_event(data: dict[str, Any], *, organization_id: str, actor: str) -> dict:
    event = ChainOfCustodyEvent(
        event_code=data.get("event_code") or f"COC-{uuid.uuid4().hex[:10].upper()}",
        event_type=data["event_type"],
        reference_type=data.get("reference_type"),
        reference_id=data.get("reference_id"),
        actor=actor,
        location=data.get("location"),
        metadata_json=json.dumps({
            "organization_id": organization_id,
            "previous_custodian": data.get("previous_custodian"),
            "new_custodian": data.get("new_custodian"),
            "reason": data.get("reason"),
            "signature_reference": data.get("signature_reference"),
            "evidence_reference": data.get("evidence_reference"),
            "correlation_id": data.get("correlation_id"),
            "device_id": data.get("device_id"),
        }),
    )
    db.session.add(event)
    return event.to_dict()


def list_custody_events(*, organization_id: str, reference_id: str | None = None, limit: int = 50) -> dict:
    q = ChainOfCustodyEvent.query
    if reference_id:
        q = q.filter_by(reference_id=reference_id)
    rows = q.order_by(ChainOfCustodyEvent.created_at.desc()).limit(limit).all()
    filtered = []
    for row in rows:
        meta = {}
        if row.metadata_json:
            try:
                meta = json.loads(row.metadata_json)
            except json.JSONDecodeError:
                pass
        if meta.get("organization_id") == organization_id or not meta.get("organization_id"):
            filtered.append(row.to_dict())
    return {"count": len(filtered), "events": filtered}


def list_vehicles(*, organization_id: str) -> dict:
    from app.models.logistics_driver import LogisticsVehicle
    rows = LogisticsVehicle.query.all()
    return {"count": len(rows), "vehicles": [r.to_dict() for r in rows]}


def list_containers(*, organization_id: str) -> dict:
    rows = TransportBox.query.order_by(TransportBox.created_at.desc()).all()
    return {"count": len(rows), "containers": [r.to_dict() for r in rows]}


def logistics_dashboard(*, organization_id: str) -> dict:
    active_trips = LogisticsTransportTrip.query.filter_by(organization_id=organization_id, status=LOGISTICS_TRIP_ACTIVE).count()
    open_alerts = IoTPlatformAlert.query.filter_by(organization_id=organization_id, status="OPEN").count()
    open_excursions = IoTColdChainExcursion.query.filter(
        IoTColdChainExcursion.organization_id == organization_id,
        IoTColdChainExcursion.state.in_([EXCURSION_DETECTED, EXCURSION_ACTIVE]),
    ).count()
    offline_cutoff = _utcnow() - timedelta(minutes=15)
    devices = IoTDevice.query
    if hasattr(IoTDevice, "organization_id"):
        devices = devices.filter(IoTDevice.organization_id == organization_id)
    offline_devices = devices.filter(
        (IoTDevice.last_seen_at.is_(None)) | (IoTDevice.last_seen_at < offline_cutoff)
    ).count()
    return {
        "organization_id": organization_id,
        "kpis": {
            "active_trips": active_trips,
            "open_alerts": open_alerts,
            "active_excursions": open_excursions,
            "offline_devices": offline_devices,
            "delayed_trips": 0,
        },
    }


def process_telemetry_batch(
    payloads: list[dict[str, Any]],
    *,
    organization_id: str,
    adapter_type: str = "HTTP_JSON",
    simulated: bool = False,
) -> dict:
    accepted, duplicates, rejected = 0, 0, 0
    results = []
    policies = IoTThresholdPolicy.query.filter_by(organization_id=organization_id, status="ACTIVE").all()
    for payload in payloads:
        try:
            result = ingest_telemetry(payload, organization_id=organization_id, adapter_type=adapter_type, simulated=simulated)
            if result.get("status") == "duplicate":
                duplicates += 1
            else:
                accepted += 1
                reading = IoTCanonicalReading.query.get(result["reading_id"])
                if reading:
                    for policy in policies:
                        evaluate_excursion(reading, policy)
                    trip = LogisticsTransportTrip.query.get(reading.trip_id) if reading.trip_id else None
                    if trip and reading.latitude is not None:
                        trip.latest_latitude = reading.latitude
                        trip.latest_longitude = reading.longitude
                        trip.latest_location_at = reading.recorded_at
            results.append(result)
        except (IngestionError, IoTPlatformError) as exc:
            rejected += 1
            results.append({"status": "rejected", "error": str(exc)})
    return {"accepted": accepted, "duplicates": duplicates, "rejected": rejected, "results": results}
