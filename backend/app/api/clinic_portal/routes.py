from flask import Blueprint, request

from app.core.authenticated_identity import (
    authenticated_actor_email,
    blueprint_require_authenticated_user,
)
from app.core.tenant_authorization import authorize_clinic_id
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
blueprint_require_authenticated_user(clinic_portal_bp)


def _client_ip():
    return request.remote_addr or ""


def _actor_email():
    # P0-A: actor from authenticated JWT/session only (never X-User-Email).
    return authenticated_actor_email()


def _clinic_id():
    """Client selector → membership-validated clinic (P0-C). Returns str or error response."""
    from app.core.tenant_authorization import client_requested_clinic_id

    return authorize_clinic_id(client_requested_clinic_id())


def _require_clinic_id():
    clinic_id = _clinic_id()
    if not isinstance(clinic_id, str):
        return None, clinic_id
    return clinic_id, None


@clinic_portal_bp.route("/dashboard", methods=["GET"])
def clinic_dashboard():
    clinic_id, err = _require_clinic_id()
    if err:
        return err
    try:
        payload = ClinicDashboardService.get_dashboard(clinic_id)
    except ClinicPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@clinic_portal_bp.route("/profile", methods=["GET"])
def get_clinic_profile():
    clinic_id, err = _require_clinic_id()
    if err:
        return err
    try:
        payload = ClinicPortalService.get_profile(clinic_id)
    except ClinicPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@clinic_portal_bp.route("/profile", methods=["PUT"])
def update_clinic_profile():
    clinic_id, err = _require_clinic_id()
    if err:
        return err
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
    clinic_id, err = _require_clinic_id()
    if err:
        return err
    try:
        payload = ClinicBookingService.list_bookings(clinic_id, status=request.args.get("status"))
    except ClinicPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@clinic_portal_bp.route("/orders", methods=["GET"])
def clinic_orders():
    clinic_id, err = _require_clinic_id()
    if err:
        return err
    try:
        payload = ClinicOrderService.list_orders(clinic_id, status=request.args.get("status"))
    except ClinicPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@clinic_portal_bp.route("/patients", methods=["GET"])
def clinic_patients():
    clinic_id, err = _require_clinic_id()
    if err:
        return err
    try:
        payload = ClinicPortalService.list_patients(clinic_id)
    except ClinicPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@clinic_portal_bp.route("/doctors", methods=["GET"])
def clinic_doctors():
    clinic_id, err = _require_clinic_id()
    if err:
        return err
    try:
        payload = ClinicPortalService.list_doctors(clinic_id)
    except ClinicPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@clinic_portal_bp.route("/revenue", methods=["GET"])
def clinic_revenue():
    clinic_id, err = _require_clinic_id()
    if err:
        return err
    try:
        payload = ClinicRevenueService.get_revenue_summary(
            clinic_id,
            period_days=int(request.args.get("period_days", 30)),
        )
    except ClinicPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload
