from flask import Blueprint, request

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


def _client_ip():
    return request.remote_addr or ""


def _actor_email():
    return request.headers.get("X-User-Email", "SYSTEM")


def _doctor_id():
    doctor_id = request.args.get("doctor_id") or request.headers.get("X-Doctor-Id")
    if request.method in ("POST", "PUT") and not doctor_id:
        data = request.get_json(silent=True) or {}
        doctor_id = data.get("doctor_id")
    return doctor_id


@doctor_portal_bp.route("/dashboard", methods=["GET"])
def doctor_dashboard():
    doctor_id = _doctor_id()
    if not doctor_id:
        return {"error": "doctor_id is required"}, 400
    try:
        payload = DoctorDashboardService.get_dashboard(doctor_id)
    except DoctorPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@doctor_portal_bp.route("/profile", methods=["GET"])
def get_doctor_profile():
    doctor_id = _doctor_id()
    if not doctor_id:
        return {"error": "doctor_id is required"}, 400
    try:
        payload = DoctorPortalService.get_profile(doctor_id)
    except DoctorPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@doctor_portal_bp.route("/profile", methods=["PUT"])
def update_doctor_profile():
    doctor_id = _doctor_id()
    if not doctor_id:
        return {"error": "doctor_id is required"}, 400
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
    doctor_id = _doctor_id()
    if not doctor_id:
        return {"error": "doctor_id is required"}, 400
    try:
        payload = DoctorPatientService.list_patients(doctor_id)
    except DoctorPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@doctor_portal_bp.route("/results", methods=["GET"])
def doctor_results():
    doctor_id = _doctor_id()
    if not doctor_id:
        return {"error": "doctor_id is required"}, 400
    try:
        payload = DoctorDashboardService.list_results(doctor_id)
    except DoctorPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@doctor_portal_bp.route("/referrals", methods=["GET"])
def list_referrals():
    doctor_id = _doctor_id()
    if not doctor_id:
        return {"error": "doctor_id is required"}, 400
    try:
        payload = DoctorReferralService.list_referrals(doctor_id, status=request.args.get("status"))
    except DoctorPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@doctor_portal_bp.route("/referrals", methods=["POST"])
def create_referral():
    doctor_id = _doctor_id()
    if not doctor_id:
        return {"error": "doctor_id is required"}, 400
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
    doctor_id = _doctor_id()
    if not doctor_id:
        return {"error": "doctor_id is required"}, 400
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
    doctor_id = _doctor_id()
    if not doctor_id:
        return {"error": "doctor_id is required"}, 400
    try:
        payload = DoctorDashboardService.get_schedule(doctor_id)
    except DoctorPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload
