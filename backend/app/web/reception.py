"""Production Reception Center web routes — Sprint 2.1."""

from __future__ import annotations

from flask import Blueprint, redirect, request, session, url_for

from app.models.patient import Patient
from app.services.reception_service import RECEPTION_ROLES, ReceptionError, check_in_appointment, check_in_queue, check_out_queue, log_activity, register_patient_quick, register_walk_in, search_patients
from app.utils.auth import role_required
from app.web.reception_lib import (
    build_activity_body,
    build_check_in_body,
    build_dashboard_body,
    build_kpi_body,
    build_quick_register_body,
    build_search_body,
    build_walk_in_body,
    render_reception_page,
)

reception_web_bp = Blueprint("reception_web", __name__)


def _actor() -> str | None:
    return session.get("email")


@reception_web_bp.route("/reception")
@role_required(*RECEPTION_ROLES)
def reception_dashboard():
    message = request.args.get("message", "")
    error = request.args.get("error", "")
    return render_reception_page("Reception Center", build_dashboard_body(message=message, error=error))


@reception_web_bp.route("/reception/search", methods=["GET"])
@role_required(*RECEPTION_ROLES)
def reception_search():
    code = request.args.get("code", "").strip()
    phone = request.args.get("phone", "").strip()
    national_id = request.args.get("national_id", "").strip()
    name = request.args.get("name", "").strip()
    results = []
    if any((code, phone, national_id, name)):
        results = search_patients(code=code or None, phone=phone or None, national_id=national_id or None, name=name or None)
        log_activity(
            "SEARCH",
            details=f"code={code} phone={phone} national_id={national_id} name={name} hits={len(results)}",
            actor_email=_actor(),
        )
        from app.extensions.db import db

        db.session.commit()
    return render_reception_page("Patient Search", build_search_body(results=results))


@reception_web_bp.route("/reception/register/quick", methods=["GET", "POST"])
@role_required(*RECEPTION_ROLES)
def reception_quick_register():
    if request.method == "GET":
        return render_reception_page("Quick Registration", build_quick_register_body())
    try:
        result = register_patient_quick(
            full_name=request.form.get("full_name", ""),
            phone=request.form.get("phone", ""),
            gender=request.form.get("gender") or None,
            actor_email=_actor(),
        )
        return redirect(
            url_for(
                "reception_web.reception_dashboard",
                message=f"Registered {result['patient_code']} · Queue {result['queue_number']}",
            )
        )
    except ReceptionError as exc:
        return render_reception_page("Quick Registration", build_quick_register_body(error=exc.message))


@reception_web_bp.route("/reception/register/walk-in", methods=["GET", "POST"])
@role_required(*RECEPTION_ROLES)
def reception_walk_in():
    defaults = {}
    patient_code = request.args.get("patient_code") or request.form.get("patient_code")
    if patient_code:
        patient = Patient.query.get(patient_code)
        if patient:
            defaults = {
                "full_name": patient.full_name,
                "phone": patient.phone or "",
                "national_id": patient.national_id or "",
                "address": patient.address or "",
            }
    if request.method == "GET":
        return render_reception_page("Walk-in Registration", build_walk_in_body(defaults=defaults))
    try:
        result = register_walk_in(
            full_name=request.form.get("full_name", ""),
            phone=request.form.get("phone", ""),
            national_id=request.form.get("national_id") or None,
            gender=request.form.get("gender") or None,
            address=request.form.get("address") or None,
            actor_email=_actor(),
        )
        return redirect(
            url_for(
                "reception_web.reception_dashboard",
                message=f"Walk-in queued · {result['patient_code']} · {result['queue_number']}",
            )
        )
    except ReceptionError as exc:
        return render_reception_page("Walk-in Registration", build_walk_in_body(error=exc.message, defaults=defaults))


@reception_web_bp.route("/reception/check-in", methods=["GET", "POST"])
@role_required(*RECEPTION_ROLES)
def reception_check_in():
    if request.method == "GET":
        return render_reception_page("Appointment Check-in", build_check_in_body())
    try:
        result = check_in_appointment(
            booking_code=request.form.get("booking_code") or None,
            patient_id=request.form.get("patient_id") or None,
            actor_email=_actor(),
        )
        return redirect(
            url_for(
                "reception_web.reception_dashboard",
                message=f"Checked in {result['booking_code']} · Queue {result['queue_number']}",
            )
        )
    except ReceptionError as exc:
        return render_reception_page("Appointment Check-in", build_check_in_body(error=exc.message))


@reception_web_bp.route("/reception/queue/<entry_id>/check-in", methods=["POST"])
@role_required(*RECEPTION_ROLES)
def reception_queue_check_in(entry_id):
    try:
        entry = check_in_queue(entry_id, actor_email=_actor())
        return redirect(url_for("reception_web.reception_dashboard", message=f"Checked in {entry.queue_number}"))
    except ReceptionError as exc:
        return redirect(url_for("reception_web.reception_dashboard", error=exc.message))


@reception_web_bp.route("/reception/queue/<entry_id>/check-out", methods=["POST"])
@role_required(*RECEPTION_ROLES)
def reception_queue_check_out(entry_id):
    try:
        entry = check_out_queue(entry_id, actor_email=_actor())
        return redirect(url_for("reception_web.reception_dashboard", message=f"Checked out {entry.queue_number}"))
    except ReceptionError as exc:
        return redirect(url_for("reception_web.reception_dashboard", error=exc.message))


@reception_web_bp.route("/reception/activity")
@role_required(*RECEPTION_ROLES)
def reception_activity():
    return render_reception_page("Reception Activity Log", build_activity_body())


@reception_web_bp.route("/reception/kpi")
@role_required(*RECEPTION_ROLES)
def reception_kpi():
    return render_reception_page("Reception KPI", build_kpi_body())
