"""IoT Logistics Platform models — Release 7.0 Sprint 4."""

from __future__ import annotations

import json
import uuid
from datetime import datetime

from app.extensions.db import db


class IoTDeviceCredential(db.Model):
    __tablename__ = "iot_device_credentials"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = db.Column(db.String(36), db.ForeignKey("iot_devices.id"), nullable=False)
    credential_hash = db.Column(db.String(255), nullable=False)
    credential_ref = db.Column(db.String(255))
    rotated_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class IoTDeviceAssignment(db.Model):
    __tablename__ = "iot_device_assignments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    device_id = db.Column(db.String(36), db.ForeignKey("iot_devices.id"), nullable=False)
    vehicle_id = db.Column(db.String(36))
    container_id = db.Column(db.String(36))
    trip_id = db.Column(db.String(36))
    assigned_by = db.Column(db.String(255))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    released_at = db.Column(db.DateTime)
    status = db.Column(db.String(30), default="ACTIVE")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "device_id": self.device_id,
            "vehicle_id": self.vehicle_id,
            "container_id": self.container_id,
            "trip_id": self.trip_id,
            "assigned_by": self.assigned_by,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "status": self.status,
        }


class IoTCanonicalReading(db.Model):
    __tablename__ = "iot_canonical_readings"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    device_id = db.Column(db.String(36), nullable=False, index=True)
    idempotency_key = db.Column(db.String(128), unique=True)
    sequence_number = db.Column(db.BigInteger)
    recorded_at = db.Column(db.DateTime, nullable=False)
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    temperature_c = db.Column(db.Float)
    humidity_percent = db.Column(db.Float)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    speed_kph = db.Column(db.Float)
    heading = db.Column(db.Float)
    altitude_m = db.Column(db.Float)
    battery_percent = db.Column(db.Float)
    signal_strength = db.Column(db.Float)
    door_open = db.Column(db.Boolean)
    trip_id = db.Column(db.String(36))
    transport_container_id = db.Column(db.String(36))
    metadata_json = db.Column(db.Text)
    simulated = db.Column(db.Boolean, default=False)

    def to_dict(self) -> dict:
        meta = {}
        if self.metadata_json:
            try:
                meta = json.loads(self.metadata_json)
            except json.JSONDecodeError:
                meta = {}
        return {
            "id": self.id,
            "device_id": self.device_id,
            "organization_id": self.organization_id,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "temperature_c": self.temperature_c,
            "humidity_percent": self.humidity_percent,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "speed_kph": self.speed_kph,
            "heading": self.heading,
            "battery_percent": self.battery_percent,
            "door_open": self.door_open,
            "trip_id": self.trip_id,
            "transport_container_id": self.transport_container_id,
            "sequence_number": self.sequence_number,
            "simulated": self.simulated,
            "metadata": meta,
        }


class IoTThresholdPolicy(db.Model):
    __tablename__ = "iot_threshold_policies"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    policy_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    specimen_type = db.Column(db.String(50))
    test_requirement = db.Column(db.String(100))
    container_type = db.Column(db.String(50))
    route_id = db.Column(db.String(36))
    min_temperature_c = db.Column(db.Float)
    max_temperature_c = db.Column(db.Float)
    min_humidity_percent = db.Column(db.Float)
    max_humidity_percent = db.Column(db.Float)
    grace_duration_seconds = db.Column(db.Integer, default=300)
    sampling_interval_seconds = db.Column(db.Integer, default=60)
    max_transport_duration_seconds = db.Column(db.Integer)
    max_door_open_seconds = db.Column(db.Integer)
    requires_calibration = db.Column(db.Boolean, default=True)
    approved_by = db.Column(db.String(255))
    approved_at = db.Column(db.DateTime)
    status = db.Column(db.String(30), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "policy_code": self.policy_code,
            "name": self.name,
            "specimen_type": self.specimen_type,
            "container_type": self.container_type,
            "min_temperature_c": self.min_temperature_c,
            "max_temperature_c": self.max_temperature_c,
            "min_humidity_percent": self.min_humidity_percent,
            "max_humidity_percent": self.max_humidity_percent,
            "grace_duration_seconds": self.grace_duration_seconds,
            "approved_by": self.approved_by,
            "status": self.status,
        }


class IoTColdChainExcursion(db.Model):
    __tablename__ = "iot_cold_chain_excursions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    device_id = db.Column(db.String(36))
    trip_id = db.Column(db.String(36))
    transport_container_id = db.Column(db.String(36))
    policy_id = db.Column(db.String(36), db.ForeignKey("iot_threshold_policies.id"))
    excursion_type = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), default="DETECTED")
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    acknowledged_by = db.Column(db.String(255))
    acknowledged_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.String(255))
    resolved_at = db.Column(db.DateTime)
    override_reason = db.Column(db.Text)
    specimen_hold = db.Column(db.Boolean, default=False)
    correlation_id = db.Column(db.String(64))
    metadata_json = db.Column(db.Text)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "device_id": self.device_id,
            "trip_id": self.trip_id,
            "excursion_type": self.excursion_type,
            "state": self.state,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "specimen_hold": self.specimen_hold,
            "correlation_id": self.correlation_id,
        }


class IoTPlatformAlert(db.Model):
    __tablename__ = "iot_platform_alerts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), default="WARNING")
    status = db.Column(db.String(30), default="OPEN")
    device_id = db.Column(db.String(36))
    trip_id = db.Column(db.String(36))
    dedupe_key = db.Column(db.String(128), unique=True)
    message = db.Column(db.Text)
    channel = db.Column(db.String(30), default="in_app")
    correlation_id = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    acknowledged_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "status": self.status,
            "device_id": self.device_id,
            "trip_id": self.trip_id,
            "message": self.message,
            "channel": self.channel,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class IoTTelemetryDeadLetter(db.Model):
    __tablename__ = "iot_telemetry_dead_letters"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36))
    device_id = db.Column(db.String(36))
    adapter_type = db.Column(db.String(30))
    error_code = db.Column(db.String(50))
    error_message = db.Column(db.Text)
    payload_ref = db.Column(db.String(255))
    received_at = db.Column(db.DateTime, default=datetime.utcnow)


class LogisticsTransportTrip(db.Model):
    __tablename__ = "logistics_transport_trips"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    trip_code = db.Column(db.String(50), unique=True, nullable=False)
    route_plan_id = db.Column(db.String(36))
    driver_profile_id = db.Column(db.String(36))
    vehicle_id = db.Column(db.String(36))
    container_id = db.Column(db.String(36))
    status = db.Column(db.String(30), default="PLANNED")
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    latest_latitude = db.Column(db.Float)
    latest_longitude = db.Column(db.Float)
    latest_location_at = db.Column(db.DateTime)
    distance_km = db.Column(db.Float, default=0)
    eta_provider = db.Column(db.String(30), default="test")
    correlation_id = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "trip_code": self.trip_code,
            "route_plan_id": self.route_plan_id,
            "driver_profile_id": self.driver_profile_id,
            "vehicle_id": self.vehicle_id,
            "container_id": self.container_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "latest_latitude": self.latest_latitude,
            "latest_longitude": self.latest_longitude,
            "latest_location_at": self.latest_location_at.isoformat() if self.latest_location_at else None,
            "distance_km": self.distance_km,
            "eta_provider": self.eta_provider,
            "correlation_id": self.correlation_id,
        }
