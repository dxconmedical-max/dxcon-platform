from flask import Blueprint, request

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
def list_devices():
    payload = IoTDeviceService.list_devices(
        status=request.args.get("status"),
        device_type=request.args.get("device_type"),
    )
    return payload


@iot_bp.route("/devices", methods=["POST"])
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
    try:
        payload = TemperatureMonitoringService.record_temperature(data)
    except IoTError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Temperature recorded", **payload}, 201


@iot_bp.route("/readings/humidity", methods=["POST"])
def record_humidity():
    data = request.get_json(silent=True) or {}
    try:
        payload = TemperatureMonitoringService.record_humidity(data)
    except IoTError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Humidity recorded", **payload}, 201


@iot_bp.route("/readings/gps", methods=["POST"])
def record_gps():
    data = request.get_json(silent=True) or {}
    try:
        payload = GPSMonitoringService.record_gps(data)
    except IoTError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "GPS recorded", **payload}, 201


@iot_bp.route("/readings/shock", methods=["POST"])
def record_shock():
    data = request.get_json(silent=True) or {}
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
