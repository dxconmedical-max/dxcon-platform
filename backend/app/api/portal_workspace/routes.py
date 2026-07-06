"""Portal workspace REST API — Sprint 009."""

from __future__ import annotations

from flask import Blueprint, request, session

from app.doctor_portal.auth import doctor_portal_note, doctor_portal_read, doctor_portal_write
from app.doctor_portal.service import (
    DoctorPortalError,
    add_favorite_patient,
    create_clinical_note,
    dashboard as doctor_dashboard,
    doctor_portal_report,
    list_favorite_patients,
    patient_profile,
    portal_security_report,
    report_detail,
    search_patients,
)
from app.extensions.db import db
from app.patient_portal.auth import patient_portal_read, patient_portal_write
from app.patient_portal.service import (
    PatientPortalError,
    add_favorite,
    dashboard as patient_dashboard,
    generate_qr_health_card,
    get_report as patient_get_report,
    grant_consent,
    list_consents,
    list_favorites,
    list_invoices,
    list_notifications,
    medical_history,
    patient_portal_report,
    revoke_consent,
    update_profile,
)

portal_doctor_bp = Blueprint("portal_doctor", __name__, url_prefix="/api/v1/portal/doctor")
portal_patient_bp = Blueprint("portal_patient", __name__, url_prefix="/api/v1/portal/patient")


def _actor() -> str | None:
    return session.get("email") or request.headers.get("X-Actor")


@portal_doctor_bp.route("/dashboard", methods=["GET"])
@doctor_portal_read
def api_doctor_dashboard():
    return {"success": True, "data": doctor_dashboard(actor=_actor())}, 200


@portal_doctor_bp.route("/patients/search", methods=["GET"])
@doctor_portal_read
def api_doctor_search():
    result = search_patients(
        q=request.args.get("q"),
        patient_code=request.args.get("patient_code"),
        name=request.args.get("name"),
        phone=request.args.get("phone"),
        order_code=request.args.get("order_code"),
        report_code=request.args.get("report_code"),
        page=int(request.args.get("page", 1)),
        per_page=int(request.args.get("per_page", 25)),
        sort=request.args.get("sort", "created_at"),
    )
    return {"success": True, **result}, 200


@portal_doctor_bp.route("/patients/<patient_code>", methods=["GET"])
@doctor_portal_read
def api_doctor_patient(patient_code: str):
    try:
        return {"success": True, "data": patient_profile(patient_code)}, 200
    except DoctorPortalError as exc:
        return {"success": False, "error": str(exc)}, 404


@portal_doctor_bp.route("/reports/<report_code>", methods=["GET"])
@doctor_portal_read
def api_doctor_report(report_code: str):
    try:
        return {"success": True, "data": report_detail(report_code, actor=_actor())}, 200
    except DoctorPortalError as exc:
        return {"success": False, "error": str(exc)}, 404


@portal_doctor_bp.route("/notes", methods=["POST"])
@doctor_portal_note
def api_doctor_note():
    payload = request.get_json(silent=True) or {}
    try:
        data = create_clinical_note(
            patient_code=payload["patient_code"],
            note_text=payload.get("note_text", ""),
            note_type=payload.get("note_type", "clinical"),
            visibility=payload.get("visibility", "internal"),
            order_code=payload.get("order_code"),
            report_code=payload.get("report_code"),
            follow_up_recommendation=payload.get("follow_up_recommendation"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": data}, 201
    except (DoctorPortalError, KeyError) as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@portal_doctor_bp.route("/favorites/patients", methods=["GET"])
@doctor_portal_read
def api_doctor_favorites():
    return {"success": True, "data": list_favorite_patients()}, 200


@portal_doctor_bp.route("/favorites/patients/<patient_code>", methods=["POST"])
@doctor_portal_write
def api_doctor_add_favorite(patient_code: str):
    data = add_favorite_patient(patient_code, label=request.json.get("label") if request.is_json else None)
    db.session.commit()
    return {"success": True, "data": data}, 201


@portal_doctor_bp.route("/report", methods=["GET"])
@doctor_portal_read
def api_doctor_portal_report():
    return {"success": True, "data": doctor_portal_report()}, 200


@portal_doctor_bp.route("/security-report", methods=["GET"])
@doctor_portal_read
def api_portal_security():
    return {"success": True, "data": portal_security_report()}, 200


@portal_patient_bp.route("/dashboard", methods=["GET"])
@patient_portal_read
def api_patient_dashboard():
    try:
        return {"success": True, "data": patient_dashboard(actor=_actor())}, 200
    except PatientPortalError as exc:
        return {"success": False, "error": str(exc)}, 400


@portal_patient_bp.route("/history", methods=["GET"])
@patient_portal_read
def api_patient_history():
    try:
        return {"success": True, "data": medical_history(event_type=request.args.get("event_type"))}, 200
    except PatientPortalError as exc:
        return {"success": False, "error": str(exc)}, 400


@portal_patient_bp.route("/reports/<report_code>", methods=["GET"])
@patient_portal_read
def api_patient_report(report_code: str):
    try:
        return {"success": True, "data": patient_get_report(report_code, actor=_actor())}, 200
    except PatientPortalError as exc:
        return {"success": False, "error": str(exc)}, 403


@portal_patient_bp.route("/invoices", methods=["GET"])
@patient_portal_read
def api_patient_invoices():
    try:
        return {"success": True, "data": list_invoices(actor=_actor())}, 200
    except PatientPortalError as exc:
        return {"success": False, "error": str(exc)}, 400


@portal_patient_bp.route("/profile", methods=["PUT"])
@patient_portal_write
def api_patient_profile():
    payload = request.get_json(silent=True) or {}
    try:
        data = update_profile(payload, actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except PatientPortalError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@portal_patient_bp.route("/notifications", methods=["GET"])
@patient_portal_read
def api_patient_notifications():
    try:
        return {"success": True, "data": list_notifications()}, 200
    except PatientPortalError as exc:
        return {"success": False, "error": str(exc)}, 400


@portal_patient_bp.route("/qr", methods=["POST"])
@patient_portal_write
def api_patient_qr():
    try:
        data = generate_qr_health_card(actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 201
    except PatientPortalError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@portal_patient_bp.route("/consent", methods=["POST"])
@patient_portal_write
def api_patient_consent():
    payload = request.get_json(silent=True) or {}
    try:
        if payload.get("granted", True):
            data = grant_consent(payload.get("consent_type", "general"), actor=_actor(), metadata=payload.get("metadata"))
        else:
            data = revoke_consent(payload.get("consent_type", "general"), actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except PatientPortalError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@portal_patient_bp.route("/consent", methods=["GET"])
@patient_portal_read
def api_patient_consent_list():
    try:
        return {"success": True, "data": list_consents()}, 200
    except PatientPortalError as exc:
        return {"success": False, "error": str(exc)}, 400


@portal_patient_bp.route("/favorites", methods=["GET", "POST"])
@patient_portal_read
def api_patient_favorites():
    if request.method == "GET":
        try:
            return {"success": True, "data": list_favorites()}, 200
        except PatientPortalError as exc:
            return {"success": False, "error": str(exc)}, 400
    payload = request.get_json(silent=True) or {}
    try:
        data = add_favorite(payload.get("favorite_type", "doctor"), payload.get("favorite_id", ""), label=payload.get("label"))
        db.session.commit()
        return {"success": True, "data": data}, 201
    except PatientPortalError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@portal_patient_bp.route("/report", methods=["GET"])
@patient_portal_read
def api_patient_portal_report():
    return {"success": True, "data": patient_portal_report()}, 200
