"""IoT Logistics Platform REST API — Release 7.0 Sprint 4."""

from __future__ import annotations

from flask import Blueprint, request, session

from app.extensions.db import db
from app.iot_platform.auth import device_ingest_auth, iot_api_read, iot_api_write
from app.iot_platform.ingestion import IngestionError, ingest_telemetry, record_dead_letter
from app.iot_platform.service import (
    IoTPlatformError,
    acknowledge_excursion,
    append_custody_event,
    create_threshold_policy,
    create_trip,
    get_device,
    get_trip,
    hold_specimen_for_excursion,
    list_alerts,
    list_containers,
    list_custody_events,
    list_devices,
    list_excursions,
    list_readings,
    list_trips,
    list_vehicles,
    logistics_dashboard,
    process_telemetry_batch,
    register_device,
    transition_trip,
    trip_locations,
    trip_timeline,
)

iot_devices_bp = Blueprint("iot_platform_devices", __name__, url_prefix="/api/v1/iot/devices")
iot_readings_bp = Blueprint("iot_platform_readings", __name__, url_prefix="/api/v1/iot/readings")
iot_telemetry_bp = Blueprint("iot_platform_telemetry", __name__, url_prefix="/api/v1/iot/telemetry")
iot_alerts_bp = Blueprint("iot_platform_alerts", __name__, url_prefix="/api/v1/iot/alerts")
iot_excursions_bp = Blueprint("iot_platform_excursions", __name__, url_prefix="/api/v1/iot/excursions")
logistics_trips_bp = Blueprint("logistics_trips", __name__, url_prefix="/api/v1/logistics/trips")
logistics_vehicles_bp = Blueprint("logistics_vehicles", __name__, url_prefix="/api/v1/logistics/vehicles")
logistics_containers_bp = Blueprint("logistics_containers", __name__, url_prefix="/api/v1/logistics/containers")
logistics_dashboard_bp = Blueprint("logistics_dashboard", __name__, url_prefix="/api/v1/logistics/dashboard")
custody_bp = Blueprint("custody_events", __name__, url_prefix="/api/v1/custody/events")


def _org() -> str:
    return request.headers.get("X-Organization-ID") or session.get("organization_id") or "default-org"


def _actor() -> str | None:
    return session.get("email") or request.headers.get("X-Actor")


@iot_devices_bp.route("", methods=["GET"])
@iot_api_read
def devices_list():
    page = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 25)), 100)
    return {"success": True, "data": list_devices(organization_id=_org(), status=request.args.get("status"), page=page, per_page=per_page)}


@iot_devices_bp.route("", methods=["POST"])
@iot_api_write
def devices_create():
    data = request.get_json(silent=True) or {}
    try:
        payload = register_device(data, organization_id=_org(), actor=_actor())
        db.session.commit()
        return {"success": True, "data": payload}, 201
    except IoTPlatformError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400


@iot_devices_bp.route("/<device_id>", methods=["GET"])
@iot_api_read
def devices_get(device_id):
    try:
        return {"success": True, "data": get_device(device_id, organization_id=_org())}
    except IoTPlatformError as exc:
        return {"error": str(exc)}, 404


@iot_readings_bp.route("", methods=["GET"])
@iot_api_read
def readings_list():
    page = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 50)), 200)
    return {
        "success": True,
        "data": list_readings(
            organization_id=_org(),
            device_id=request.args.get("device_id"),
            trip_id=request.args.get("trip_id"),
            page=page,
            per_page=per_page,
        ),
    }


@iot_telemetry_bp.route("", methods=["POST"])
@device_ingest_auth
def telemetry_ingest():
    data = request.get_json(silent=True) or {}
    adapter = request.headers.get("X-IoT-Adapter", data.get("adapter_type", "HTTP_JSON"))
    simulated = bool(data.get("simulated"))
    payloads = data.get("readings") or [data.get("payload") or data]
    try:
        result = process_telemetry_batch(payloads, organization_id=_org(), adapter_type=adapter, simulated=simulated)
        db.session.commit()
        return {"success": True, "data": result}, 201
    except IngestionError as exc:
        db.session.rollback()
        record_dead_letter(organization_id=_org(), device_id=data.get("device_id"), adapter_type=adapter, error_code="INGEST", error_message=str(exc))
        db.session.commit()
        return {"error": str(exc)}, 400


@iot_alerts_bp.route("", methods=["GET"])
@iot_api_read
def alerts_list():
    page = int(request.args.get("page", 1))
    return {"success": True, "data": list_alerts(organization_id=_org(), status=request.args.get("status"), page=page)}


@iot_excursions_bp.route("", methods=["GET"])
@iot_api_read
def excursions_list():
    return {"success": True, "data": list_excursions(organization_id=_org(), state=request.args.get("state"))}


@iot_excursions_bp.route("/<excursion_id>/acknowledge", methods=["POST"])
@iot_api_write
def excursions_ack(excursion_id):
    try:
        payload = acknowledge_excursion(excursion_id, actor=_actor() or "system", organization_id=_org())
        db.session.commit()
        return {"success": True, "data": payload}
    except IoTPlatformError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 404


@iot_excursions_bp.route("/<excursion_id>/hold", methods=["POST"])
@iot_api_write
def excursions_hold(excursion_id):
    try:
        payload = hold_specimen_for_excursion(excursion_id, actor=_actor() or "system", organization_id=_org())
        db.session.commit()
        return {"success": True, "data": payload}
    except IoTPlatformError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 404


@logistics_trips_bp.route("", methods=["GET"])
@iot_api_read
def trips_list():
    page = int(request.args.get("page", 1))
    return {"success": True, "data": list_trips(organization_id=_org(), status=request.args.get("status"), page=page)}


@logistics_trips_bp.route("", methods=["POST"])
@iot_api_write
def trips_create():
    data = request.get_json(silent=True) or {}
    try:
        payload = create_trip(data, organization_id=_org())
        db.session.commit()
        return {"success": True, "data": payload}, 201
    except IoTPlatformError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400


@logistics_trips_bp.route("/<trip_id>", methods=["GET"])
@iot_api_read
def trips_get(trip_id):
    try:
        return {"success": True, "data": get_trip(trip_id, organization_id=_org())}
    except IoTPlatformError as exc:
        return {"error": str(exc)}, 404


@logistics_trips_bp.route("/<trip_id>/locations", methods=["GET"])
@iot_api_read
def trips_locations(trip_id):
    try:
        return {"success": True, "data": trip_locations(trip_id, organization_id=_org())}
    except IoTPlatformError as exc:
        return {"error": str(exc)}, 404


@logistics_trips_bp.route("/<trip_id>/timeline", methods=["GET"])
@iot_api_read
def trips_timeline(trip_id):
    try:
        return {"success": True, "data": trip_timeline(trip_id, organization_id=_org())}
    except IoTPlatformError as exc:
        return {"error": str(exc)}, 404


@logistics_trips_bp.route("/<trip_id>/transition", methods=["POST"])
@iot_api_write
def trips_transition(trip_id):
    data = request.get_json(silent=True) or {}
    try:
        payload = transition_trip(trip_id, action=data.get("action", "start"), organization_id=_org(), actor=_actor())
        db.session.commit()
        return {"success": True, "data": payload}
    except IoTPlatformError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400


@logistics_vehicles_bp.route("", methods=["GET"])
@iot_api_read
def vehicles_list():
    return {"success": True, "data": list_vehicles(organization_id=_org())}


@logistics_containers_bp.route("", methods=["GET"])
@iot_api_read
def containers_list():
    return {"success": True, "data": list_containers(organization_id=_org())}


@logistics_dashboard_bp.route("", methods=["GET"])
@iot_api_read
def dashboard():
    return {"success": True, "data": logistics_dashboard(organization_id=_org())}


@custody_bp.route("", methods=["GET"])
@iot_api_read
def custody_list():
    return {
        "success": True,
        "data": list_custody_events(
            organization_id=_org(),
            reference_id=request.args.get("reference_id"),
            limit=int(request.args.get("limit", 50)),
        ),
    }


@custody_bp.route("", methods=["POST"])
@iot_api_write
def custody_create():
    data = request.get_json(silent=True) or {}
    try:
        payload = append_custody_event(data, organization_id=_org(), actor=_actor() or "system")
        db.session.commit()
        return {"success": True, "data": payload}, 201
    except IoTPlatformError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400
