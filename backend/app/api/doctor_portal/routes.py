from flask import Blueprint, request

from app.core.authenticated_identity import (
    authenticated_actor_email,
    blueprint_require_authenticated_user,
)
from app.core.tenant_authorization import authorize_doctor_id, client_requested_doctor_id
from app.services.doctor_portal_service import (
    DoctorDashboardService,
    DoctorFollowUpService,
    DoctorPatientService,
    DoctorPortalError,
    DoctorPortalService,
    DoctorReferralService,
)


doctor_portal_bp = Blueprint(
    "doctor_portal",
    __name__,
    url_prefix="/api/v1/doctor",
)
blueprint_require_authenticated_user(doctor_portal_bp)


def _client_ip():
    return request.remote_addr or ""


def _actor_email():
    # P0-A: actor from authenticated JWT/session only (never X-User-Email).
    return authenticated_actor_email()


def _require_doctor_id():
    result = authorize_doctor_id(client_requested_doctor_id())
    if not isinstance(result, str):
        return None, result
    return result, None


@doctor_portal_bp.route("/dashboard", methods=["GET"])
def doctor_dashboard():
    doctor_id, err = _require_doctor_id()
    if err:
        return err
    try:
        payload = DoctorDashboardService.get_dashboard(doctor_id)
    except DoctorPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@doctor_portal_bp.route("/profile", methods=["GET"])
def get_doctor_profile():
    doctor_id, err = _require_doctor_id()
    if err:
        return err
    try:
        payload = DoctorPortalService.get_profile(doctor_id)
    except DoctorPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@doctor_portal_bp.route("/profile", methods=["PUT"])
def update_doctor_profile():
    doctor_id, err = _require_doctor_id()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    try:
        payload = DoctorPortalService.update_profile(
            doctor_id,
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except DoctorPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Profile updated", "profile": payload}


@doctor_portal_bp.route("/patients", methods=["GET"])
def doctor_patients():
    doctor_id, err = _require_doctor_id()
    if err:
        return err
    try:
        payload = DoctorPatientService.list_patients(doctor_id)
    except DoctorPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@doctor_portal_bp.route("/results", methods=["GET"])
def doctor_results():
    doctor_id, err = _require_doctor_id()
    if err:
        return err
    try:
        payload = DoctorDashboardService.list_results(doctor_id)
    except DoctorPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@doctor_portal_bp.route("/referrals", methods=["GET"])
def list_referrals():
    doctor_id, err = _require_doctor_id()
    if err:
        return err
    try:
        payload = DoctorReferralService.list_referrals(doctor_id, status=request.args.get("status"))
    except DoctorPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@doctor_portal_bp.route("/referrals", methods=["POST"])
def create_referral():
    doctor_id, err = _require_doctor_id()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    try:
        referral = DoctorReferralService.create_referral(
            doctor_id,
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except DoctorPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Referral created", "referral": referral.to_dict()}, 201


@doctor_portal_bp.route("/followups", methods=["POST"])
def create_follow_up():
    doctor_id, err = _require_doctor_id()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    try:
        follow_up = DoctorFollowUpService.create_follow_up(
            doctor_id,
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except DoctorPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Follow-up created", "follow_up": follow_up.to_dict()}, 201


@doctor_portal_bp.route("/schedule", methods=["GET"])
def doctor_schedule():
    doctor_id, err = _require_doctor_id()
    if err:
        return err
    try:
        payload = DoctorDashboardService.get_schedule(doctor_id)
    except DoctorPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload
