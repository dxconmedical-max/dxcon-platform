from flask import Blueprint, request, session

from app.models.patient import Patient
from app.models.reception_queue_entry import ReceptionQueueEntry
from app.models.clinic_booking import ClinicBooking
from app.reception_workspace.auth import reception_api_read
from app.services.reception_service import (
    ReceptionError,
    check_in_appointment,
    check_in_queue,
    check_out_queue,
    dashboard_payload,
    get_kpis,
    recent_activity,
    register_patient_quick,
    register_walk_in,
    search_patients,
)

reception_bp = Blueprint("reception_api", __name__, url_prefix="/api/v1/reception")


@reception_bp.route("/dashboard", methods=["GET"])
def reception_dashboard_api():
    return dashboard_payload()


@reception_bp.route("/search", methods=["GET"])
def reception_search_api():
    patients = search_patients(
        code=request.args.get("code"),
        phone=request.args.get("phone"),
        national_id=request.args.get("national_id"),
        name=request.args.get("name"),
    )
    return {"count": len(patients), "patients": [p.to_dict() for p in patients]}


@reception_bp.route("/register/quick", methods=["POST"])
def reception_quick_register_api():
    data = request.get_json(silent=True) or {}
    try:
        result = register_patient_quick(
            full_name=data.get("full_name", ""),
            phone=data.get("phone", ""),
            gender=data.get("gender"),
            actor_email=session.get("email"),
        )
        patient = Patient.query.filter_by(patient_code=result["patient_code"]).first()
        queue_entry = ReceptionQueueEntry.query.filter_by(queue_number=result["queue_number"]).first()
        return {
            "patient": patient.to_dict() if patient else {"patient_code": result["patient_code"]},
            "queue_entry": queue_entry.to_dict() if queue_entry else {"queue_number": result["queue_number"]},
        }, 201
    except ReceptionError as exc:
        return {"error": exc.message}, exc.status_code


@reception_bp.route("/register/walk-in", methods=["POST"])
def reception_walk_in_api():
    data = request.get_json(silent=True) or {}
    try:
        result = register_walk_in(
            full_name=data.get("full_name", ""),
            phone=data.get("phone", ""),
            national_id=data.get("national_id"),
            gender=data.get("gender"),
            address=data.get("address"),
            actor_email=session.get("email"),
        )
        patient = Patient.query.filter_by(patient_code=result["patient_code"]).first()
        queue_entry = ReceptionQueueEntry.query.filter_by(queue_number=result["queue_number"]).first()
        return {
            "patient": patient.to_dict() if patient else {"patient_code": result["patient_code"]},
            "queue_entry": queue_entry.to_dict() if queue_entry else {"queue_number": result["queue_number"]},
        }, 201
    except ReceptionError as exc:
        return {"error": exc.message}, exc.status_code


@reception_bp.route("/check-in", methods=["POST"])
def reception_check_in_api():
    data = request.get_json(silent=True) or {}
    try:
        result = check_in_appointment(
            booking_code=data.get("booking_code"),
            patient_id=data.get("patient_id"),
            actor_email=session.get("email"),
        )
        booking = ClinicBooking.query.filter_by(booking_code=result["booking_code"]).first()
        queue_entry = ReceptionQueueEntry.query.filter_by(queue_number=result["queue_number"]).first()
        return {
            "booking": booking.to_dict() if booking else {"booking_code": result["booking_code"]},
            "queue_entry": queue_entry.to_dict() if queue_entry else {"queue_number": result["queue_number"]},
        }
    except ReceptionError as exc:
        return {"error": exc.message}, exc.status_code


@reception_bp.route("/queue/<entry_id>/check-in", methods=["POST"])
def reception_queue_check_in_api(entry_id):
    try:
        entry = check_in_queue(entry_id, actor_email=session.get("email"))
        return {"queue_entry": entry.to_dict()}
    except ReceptionError as exc:
        return {"error": exc.message}, exc.status_code


@reception_bp.route("/queue/<entry_id>/check-out", methods=["POST"])
def reception_queue_check_out_api(entry_id):
    try:
        entry = check_out_queue(entry_id, actor_email=session.get("email"))
        return {"queue_entry": entry.to_dict()}
    except ReceptionError as exc:
        return {"error": exc.message}, exc.status_code


@reception_bp.route("/activity", methods=["GET"])
def reception_activity_api():
    limit = int(request.args.get("limit", 50))
    items = recent_activity(limit)
    return {"count": len(items), "activity": [item.to_dict() for item in items]}


@reception_bp.route("/kpi", methods=["GET"])
def reception_kpi_api():
    return get_kpis()


@reception_bp.route("/field-requests", methods=["GET"])
@reception_api_read
def reception_field_requests_api():
    """Canonical: GET /api/v1/reception/field-requests → HOME/CLINIC SampleCollections."""
    from app.sample_collection_workspace.collection_routing import list_home_field_requests

    try:
        payload = list_home_field_requests(
            status=request.args.get("status"),
            role=session.get("role") or request.headers.get("X-User-Role"),
            organization_id=request.headers.get("X-Organization-ID")
            or request.headers.get("X-Organization-Id"),
            limit=int(request.args.get("limit") or 200),
        )
        return {"success": True, "data": payload}, 200
    except Exception as exc:
        return {"success": False, "error": str(exc)}, 400
