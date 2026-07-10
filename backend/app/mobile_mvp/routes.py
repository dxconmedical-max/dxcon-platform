"""Mobile MVP API routes — Epic 7."""

from __future__ import annotations

from flask import Blueprint, request

from app.core.jwt_auth import require_active_user
from app.mobile_mvp.service import MobileMvpError, MobileMvpService

mobile_mvp_bp = Blueprint("mobile_mvp", __name__, url_prefix="/api/v1/mobile")


def _org_id() -> str | None:
    return request.headers.get("X-Organization-Id")


@mobile_mvp_bp.route("/app-config", methods=["GET"])
def app_config():
    return {"success": True, "data": MobileMvpService.app_config()}


@mobile_mvp_bp.route("/devices", methods=["POST"])
def register_device():
    active = require_active_user()
    if not isinstance(active, tuple):
        return active
    user, _claims = active
    data = request.get_json(silent=True) or {}
    try:
        device = MobileMvpService.register_device(user.id, {**data, "organization_id": _org_id()})
    except MobileMvpError as exc:
        return {"success": False, "error": exc.message, "code": exc.code}, exc.status_code
    return {"success": True, "data": device}, 201


@mobile_mvp_bp.route("/devices/<device_id>", methods=["DELETE"])
def revoke_device(device_id: str):
    active = require_active_user()
    if not isinstance(active, tuple):
        return active
    user, _claims = active
    try:
        device = MobileMvpService.revoke_device(user.id, device_id)
    except MobileMvpError as exc:
        return {"success": False, "error": exc.message, "code": exc.code}, exc.status_code
    return {"success": True, "data": device}


@mobile_mvp_bp.route("/patient/dashboard", methods=["GET"])
def patient_dashboard():
    active = require_active_user()
    if not isinstance(active, tuple):
        return active
    user, _claims = active
    return {"success": True, "data": MobileMvpService.patient_dashboard(user.id, _org_id())}


@mobile_mvp_bp.route("/patient/bookings", methods=["GET"])
def patient_bookings():
    active = require_active_user()
    if not isinstance(active, tuple):
        return active
    user, _claims = active
    bookings = MobileMvpService.patient_bookings(user.id, _org_id())
    return {"success": True, "data": bookings, "count": len(bookings)}


@mobile_mvp_bp.route("/patient/bookings/<booking_id>", methods=["GET"])
def patient_booking_detail(booking_id: str):
    active = require_active_user()
    if not isinstance(active, tuple):
        return active
    user, _claims = active
    try:
        data = MobileMvpService.patient_booking_detail(user.id, booking_id)
    except MobileMvpError as exc:
        return {"success": False, "error": exc.message, "code": exc.code}, exc.status_code
    return {"success": True, "data": data}


@mobile_mvp_bp.route("/patient/bookings/<booking_id>/collector-tracking", methods=["GET"])
def patient_collector_tracking(booking_id: str):
    active = require_active_user()
    if not isinstance(active, tuple):
        return active
    user, _claims = active
    try:
        data = MobileMvpService.patient_collector_tracking(user.id, booking_id)
    except MobileMvpError as exc:
        return {"success": False, "error": exc.message, "code": exc.code}, exc.status_code
    return {"success": True, "data": data}


@mobile_mvp_bp.route("/patient/results", methods=["GET"])
def patient_results():
    active = require_active_user()
    if not isinstance(active, tuple):
        return active
    user, _claims = active
    results = MobileMvpService.patient_released_results(user.id)
    return {"success": True, "data": results, "count": len(results)}


@mobile_mvp_bp.route("/patient/results/<report_code>", methods=["GET"])
def patient_result_detail(report_code: str):
    active = require_active_user()
    if not isinstance(active, tuple):
        return active
    user, _claims = active
    try:
        data = MobileMvpService.patient_result_detail(user.id, report_code)
    except MobileMvpError as exc:
        return {"success": False, "error": exc.message, "code": exc.code}, exc.status_code
    return {"success": True, "data": data}


@mobile_mvp_bp.route("/patient/notifications", methods=["GET"])
def patient_notifications():
    active = require_active_user()
    if not isinstance(active, tuple):
        return active
    user, _claims = active
    rows = MobileMvpService.patient_notifications(user.id)
    return {"success": True, "data": rows, "count": len(rows)}


@mobile_mvp_bp.route("/patient/family-profiles", methods=["GET"])
def patient_family_profiles():
    active = require_active_user()
    if not isinstance(active, tuple):
        return active
    user, _claims = active
    profiles = MobileMvpService.patient_family_profiles(user.id)
    return {"success": True, "data": profiles}


@mobile_mvp_bp.route("/collector/dashboard", methods=["GET"])
def collector_dashboard():
    active = require_active_user()
    if not isinstance(active, tuple):
        return active
    user, _claims = active
    collector_id = request.args.get("collector_id")
    if not collector_id:
        return {"success": False, "error": "collector_id required", "code": "COLLECTOR_ID_REQUIRED"}, 400
    try:
        data = MobileMvpService.collector_dashboard(collector_id, user.id)
    except MobileMvpError as exc:
        return {"success": False, "error": exc.message, "code": exc.code}, exc.status_code
    return {"success": True, "data": data}


@mobile_mvp_bp.route("/collector/jobs", methods=["GET"])
def collector_jobs():
    active = require_active_user()
    if not isinstance(active, tuple):
        return active
    user, _claims = active
    collector_id = request.args.get("collector_id")
    if not collector_id:
        return {"success": False, "error": "collector_id required", "code": "COLLECTOR_ID_REQUIRED"}, 400
    try:
        jobs = MobileMvpService.collector_jobs(collector_id, user.id, request.args.get("status"))
    except MobileMvpError as exc:
        return {"success": False, "error": exc.message, "code": exc.code}, exc.status_code
    return {"success": True, "data": jobs, "count": len(jobs)}


@mobile_mvp_bp.route("/collector/jobs/<assignment_id>", methods=["GET"])
def collector_job_detail(assignment_id: str):
    active = require_active_user()
    if not isinstance(active, tuple):
        return active
    user, _claims = active
    collector_id = request.args.get("collector_id")
    if not collector_id:
        return {"success": False, "error": "collector_id required", "code": "COLLECTOR_ID_REQUIRED"}, 400
    try:
        data = MobileMvpService.collector_job_detail(collector_id, user.id, assignment_id)
    except MobileMvpError as exc:
        return {"success": False, "error": exc.message, "code": exc.code}, exc.status_code
    return {"success": True, "data": data}


@mobile_mvp_bp.route("/collector/assignments/<assignment_id>/reject", methods=["POST"])
def reject_assignment(assignment_id: str):
    active = require_active_user()
    if not isinstance(active, tuple):
        return active
    user, _claims = active
    data = request.get_json(silent=True) or {}
    collector_id = data.get("collector_id")
    if not collector_id:
        return {"success": False, "error": "collector_id required", "code": "COLLECTOR_ID_REQUIRED"}, 400
    try:
        result = MobileMvpService.reject_assignment(collector_id, user.id, assignment_id, data.get("reason", ""))
    except MobileMvpError as exc:
        return {"success": False, "error": exc.message, "code": exc.code}, exc.status_code
    return {"success": True, "data": result}


@mobile_mvp_bp.route("/audit/events", methods=["POST"])
def record_audit_events():
    active = require_active_user()
    if not isinstance(active, tuple):
        return active
    user, _claims = active
    data = request.get_json(silent=True) or {}
    result = MobileMvpService.record_audit_batch(user.id, data.get("events", []))
    return {"success": True, "data": result}
