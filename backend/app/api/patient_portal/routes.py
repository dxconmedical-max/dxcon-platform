from flask import Blueprint, request

from app.services.patient_portal_service import (
    ConsentService,
    MedicalHistoryService,
    PatientDashboardService,
    PatientPortalError,
    PatientPortalService,
    TimelineService,
)


patient_portal_bp = Blueprint(
    "patient_portal",
    __name__,
    url_prefix="/api/v1/patient",
)


def _client_ip():
    return request.remote_addr or ""


def _actor_email():
    return request.headers.get("X-User-Email", "SYSTEM")


def _patient_id():
    patient_id = request.args.get("patient_id") or request.headers.get("X-Patient-Id")
    if request.method in ("POST", "PUT") and not patient_id:
        data = request.get_json(silent=True) or {}
        patient_id = data.get("patient_id")
    return patient_id


@patient_portal_bp.route("/dashboard", methods=["GET"])
def patient_dashboard():
    patient_id = _patient_id()
    if not patient_id:
        return {"error": "patient_id is required"}, 400
    try:
        payload = PatientDashboardService.get_dashboard(patient_id)
    except PatientPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@patient_portal_bp.route("/profile", methods=["GET"])
def get_patient_profile():
    patient_id = _patient_id()
    if not patient_id:
        return {"error": "patient_id is required"}, 400
    try:
        payload = MedicalHistoryService.get_profile(patient_id)
    except PatientPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@patient_portal_bp.route("/profile", methods=["PUT"])
def update_patient_profile():
    patient_id = _patient_id()
    if not patient_id:
        return {"error": "patient_id is required"}, 400
    data = request.get_json(silent=True) or {}
    try:
        payload = MedicalHistoryService.update_profile(
            patient_id,
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except PatientPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Profile updated", "profile": payload}


@patient_portal_bp.route("/results", methods=["GET"])
def patient_results():
    patient_id = _patient_id()
    if not patient_id:
        return {"error": "patient_id is required"}, 400
    try:
        payload = MedicalHistoryService.list_results(patient_id)
    except PatientPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@patient_portal_bp.route("/orders", methods=["GET"])
def patient_orders():
    patient_id = _patient_id()
    if not patient_id:
        return {"error": "patient_id is required"}, 400
    try:
        payload = MedicalHistoryService.list_orders(patient_id)
    except PatientPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@patient_portal_bp.route("/timeline", methods=["GET"])
def patient_timeline():
    patient_id = _patient_id()
    if not patient_id:
        return {"error": "patient_id is required"}, 400
    try:
        payload = TimelineService.get_timeline(patient_id)
    except PatientPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@patient_portal_bp.route("/notifications", methods=["GET"])
def patient_notifications():
    patient_id = _patient_id()
    if not patient_id:
        return {"error": "patient_id is required"}, 400
    try:
        payload = PatientPortalService.get_notifications(patient_id)
    except PatientPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@patient_portal_bp.route("/share-report", methods=["POST"])
def share_report():
    patient_id = _patient_id()
    if not patient_id:
        return {"error": "patient_id is required"}, 400
    data = request.get_json(silent=True) or {}
    try:
        payload = PatientPortalService.share_report(
            patient_id,
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except PatientPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Report shared", "share": payload}, 201


@patient_portal_bp.route("/consent", methods=["POST"])
def patient_consent():
    patient_id = _patient_id()
    if not patient_id:
        return {"error": "patient_id is required"}, 400
    data = request.get_json(silent=True) or {}
    try:
        payload = ConsentService.record_consent(
            patient_id,
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except PatientPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Consent recorded", "consent": payload}, 201
