from flask import Blueprint, request

from app.services.clinic_portal_service import (
    ClinicBookingService,
    ClinicDashboardService,
    ClinicOrderService,
    ClinicPortalError,
    ClinicPortalService,
    ClinicRevenueService,
)


clinic_portal_bp = Blueprint(
    "clinic_portal",
    __name__,
    url_prefix="/api/v1/clinic",
)


def _client_ip():
    return request.remote_addr or ""


def _actor_email():
    return request.headers.get("X-User-Email", "SYSTEM")


def _clinic_id():
    clinic_id = request.args.get("clinic_id") or request.headers.get("X-Clinic-Id")
    if request.method in ("POST", "PUT") and not clinic_id:
        data = request.get_json(silent=True) or {}
        clinic_id = data.get("clinic_id")
    return clinic_id


@clinic_portal_bp.route("/dashboard", methods=["GET"])
def clinic_dashboard():
    clinic_id = _clinic_id()
    if not clinic_id:
        return {"error": "clinic_id is required"}, 400
    try:
        payload = ClinicDashboardService.get_dashboard(clinic_id)
    except ClinicPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@clinic_portal_bp.route("/profile", methods=["GET"])
def get_clinic_profile():
    clinic_id = _clinic_id()
    if not clinic_id:
        return {"error": "clinic_id is required"}, 400
    try:
        payload = ClinicPortalService.get_profile(clinic_id)
    except ClinicPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@clinic_portal_bp.route("/profile", methods=["PUT"])
def update_clinic_profile():
    clinic_id = _clinic_id()
    if not clinic_id:
        return {"error": "clinic_id is required"}, 400
    data = request.get_json(silent=True) or {}
    try:
        payload = ClinicPortalService.update_profile(
            clinic_id,
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except ClinicPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Profile updated", "profile": payload}


@clinic_portal_bp.route("/bookings", methods=["GET"])
def clinic_bookings():
    clinic_id = _clinic_id()
    if not clinic_id:
        return {"error": "clinic_id is required"}, 400
    try:
        payload = ClinicBookingService.list_bookings(clinic_id, status=request.args.get("status"))
    except ClinicPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@clinic_portal_bp.route("/orders", methods=["GET"])
def clinic_orders():
    clinic_id = _clinic_id()
    if not clinic_id:
        return {"error": "clinic_id is required"}, 400
    try:
        payload = ClinicOrderService.list_orders(clinic_id, status=request.args.get("status"))
    except ClinicPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@clinic_portal_bp.route("/patients", methods=["GET"])
def clinic_patients():
    clinic_id = _clinic_id()
    if not clinic_id:
        return {"error": "clinic_id is required"}, 400
    try:
        payload = ClinicPortalService.list_patients(clinic_id)
    except ClinicPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@clinic_portal_bp.route("/doctors", methods=["GET"])
def clinic_doctors():
    clinic_id = _clinic_id()
    if not clinic_id:
        return {"error": "clinic_id is required"}, 400
    try:
        payload = ClinicPortalService.list_doctors(clinic_id)
    except ClinicPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@clinic_portal_bp.route("/revenue", methods=["GET"])
def clinic_revenue():
    clinic_id = _clinic_id()
    if not clinic_id:
        return {"error": "clinic_id is required"}, 400
    try:
        payload = ClinicRevenueService.get_revenue_summary(
            clinic_id,
            period_days=int(request.args.get("period_days", 30)),
        )
    except ClinicPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload
