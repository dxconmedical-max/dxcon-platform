"""Reporting engine REST API — Sprint 008."""

from __future__ import annotations

from flask import Blueprint, Response, request, session

from app.business_engine.service import BusinessEngineError
from app.extensions.db import db
from app.reporting_engine.auth import patient_report_read, report_api_approve, report_api_read, report_api_release, report_api_write
from app.reporting_engine.service import (
    ReportingEngineError,
    acknowledge_critical,
    approve_report,
    audit_timeline,
    create_report_amendment,
    doctor_review_report,
    get_report_pdf,
    patient_released_reports,
    production_report_pdf_report,
    reject_report,
    release_report,
    report_security_report,
    reporting_engine_report,
    request_repeat,
    review_detail,
    review_queue,
    search_reports,
    start_review,
    critical_result_report,
    report_versions,
    verify_clinical_report,
)
from app.reporting_engine.report_generation_service import build_report_payload, prepare_pdf_payload, render_html_report
from app.models.clinical_report import ClinicalReport, CriticalResultAlert

reporting_engine_bp = Blueprint("reporting_engine", __name__, url_prefix="/api/v1/reporting")


def _actor() -> str | None:
    return session.get("email") or request.headers.get("X-Actor")


def _pdf_response(bundle: dict) -> Response:
    return Response(
        bundle["bytes"],
        mimetype=bundle["content_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{bundle["filename"]}"',
            "X-Report-Code": bundle["report_code"],
            "X-Report-Version": str(bundle["report_version"]),
            "X-Report-Hash": bundle.get("report_hash") or "",
            "X-Report-Template": f"{bundle.get('template_id')}@{bundle.get('template_version')}",
            "X-Report-Reprint": str(bundle.get("reprint_number") or 0),
            "Cache-Control": "no-store",
        },
    )

@reporting_engine_bp.route("/review-queue", methods=["GET"])
@report_api_read
def api_review_queue():
    result = review_queue(
        patient=request.args.get("patient"),
        order_code=request.args.get("order_code"),
        critical_only=request.args.get("critical_only") == "1",
        status=request.args.get("status"),
        page=int(request.args.get("page", 1)),
        per_page=int(request.args.get("per_page", 25)),
    )
    return {"success": True, **result}, 200


@reporting_engine_bp.route("/review/<order_ref>", methods=["GET"])
@report_api_read
def api_review_detail(order_ref: str):
    try:
        return {"success": True, "data": review_detail(order_ref)}, 200
    except ReportingEngineError as exc:
        return {"success": False, "error": str(exc)}, 404


@reporting_engine_bp.route("/review/<order_ref>/start", methods=["POST"])
@report_api_write
def api_start_review(order_ref: str):
    try:
        data = start_review(order_ref, actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except ReportingEngineError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@reporting_engine_bp.route("/review/<order_ref>/approve", methods=["POST"])
@report_api_approve
def api_approve(order_ref: str):
    payload = request.get_json(silent=True) or {}
    try:
        data = approve_report(order_ref, doctor_note=payload.get("doctor_note"), actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except (ReportingEngineError, BusinessEngineError) as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@reporting_engine_bp.route("/review/<order_ref>/reject", methods=["POST"])
@report_api_approve
def api_reject(order_ref: str):
    payload = request.get_json(silent=True) or {}
    try:
        data = reject_report(order_ref, reason=payload.get("reason"), actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except ReportingEngineError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@reporting_engine_bp.route("/review/<order_ref>/repeat", methods=["POST"])
@report_api_approve
def api_repeat(order_ref: str):
    payload = request.get_json(silent=True) or {}
    try:
        data = request_repeat(order_ref, reason=payload.get("reason"), actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except ReportingEngineError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@reporting_engine_bp.route("/review/<order_ref>/release", methods=["POST"])
@report_api_release
def api_release(order_ref: str):
    try:
        data = release_report(order_ref, actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except (ReportingEngineError, BusinessEngineError) as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@reporting_engine_bp.route("/reports", methods=["GET"])
@report_api_read
def api_search_reports():
    result = search_reports(
        patient=request.args.get("patient"),
        order_code=request.args.get("order_code"),
        report_code=request.args.get("report_code"),
        status=request.args.get("status"),
        page=int(request.args.get("page", 1)),
        per_page=int(request.args.get("per_page", 25)),
    )
    return {"success": True, **result}, 200


@reporting_engine_bp.route("/reports/<report_code>/preview", methods=["GET"])
@report_api_read
def api_preview(report_code: str):
    report = ClinicalReport.query.filter_by(report_code=report_code).first()
    if not report:
        return {"success": False, "error": "not found"}, 404
    payload = build_report_payload(report.order_id)
    html = report.html_content or render_html_report(
        payload,
        report_code=report.report_code,
        doctor_note=report.doctor_note,
        report_version=report.report_version,
        report_status=report.report_status,
        report_hash=report.report_hash,
        approved_by=report.approved_by,
        approved_at=report.approved_at.isoformat() if report.approved_at else None,
        amendment_reason=report.amendment_reason,
    )
    return {
        "success": True,
        "data": {
            "html": html,
            "pdf_payload": prepare_pdf_payload(
                payload,
                html,
                pdf_ready=bool(report.pdf_path),
                pdf_path=report.pdf_path,
            ),
            "pdf_available": bool(report.pdf_path) and report.report_status in ("approved", "released", "amended"),
        },
    }, 200


@reporting_engine_bp.route("/reports/<report_code>/pdf", methods=["GET"])
@report_api_read
def api_report_pdf(report_code: str):
    try:
        bundle = get_report_pdf(report_code, actor=_actor(), as_reprint=False)
        return _pdf_response(bundle)
    except ReportingEngineError as exc:
        return {"success": False, "error": str(exc)}, 403 if "only after" in str(exc).lower() or "not visible" in str(exc).lower() else 404


@reporting_engine_bp.route("/reports/<report_code>/reprint", methods=["POST"])
@report_api_read
def api_report_reprint(report_code: str):
    try:
        bundle = get_report_pdf(report_code, actor=_actor(), as_reprint=True)
        db.session.commit()
        return _pdf_response(bundle)
    except ReportingEngineError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@reporting_engine_bp.route("/patient/<patient_code>/reports/<report_code>/pdf", methods=["GET"])
@patient_report_read
def api_patient_report_pdf(patient_code: str, report_code: str):
    try:
        bundle = get_report_pdf(report_code, actor=_actor(), patient_code=patient_code)
        return _pdf_response(bundle)
    except ReportingEngineError as exc:
        return {"success": False, "error": str(exc)}, 403


@reporting_engine_bp.route("/verify/<report_code>", methods=["GET"])
def api_verify_report(report_code: str):
    """Public authenticity check — minimal certificate fields only."""
    data = verify_clinical_report(report_code, hash_prefix=request.args.get("hash"))
    status = 200 if data.get("valid") else 404
    return {"success": bool(data.get("valid")), "data": data}, status


@reporting_engine_bp.route("/reports/<report_code>/versions", methods=["GET"])
@report_api_read
def api_versions(report_code: str):
    return {"success": True, "data": report_versions(report_code)}, 200


@reporting_engine_bp.route("/reports/<report_code>/audit", methods=["GET"])
@report_api_read
def api_audit(report_code: str):
    return {"success": True, "data": audit_timeline(report_code)}, 200


@reporting_engine_bp.route("/reports/<report_code>/amend", methods=["POST"])
@report_api_approve
def api_amend(report_code: str):
    payload = request.get_json(silent=True) or {}
    try:
        data = create_report_amendment(report_code, reason=payload.get("reason", ""), actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 201
    except ReportingEngineError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@reporting_engine_bp.route("/critical", methods=["GET"])
@report_api_read
def api_critical_list():
    rows = CriticalResultAlert.query.order_by(CriticalResultAlert.created_at.desc()).limit(100).all()
    return {"success": True, "data": [r.to_dict() for r in rows]}, 200


@reporting_engine_bp.route("/critical/<alert_id>/acknowledge", methods=["POST"])
@report_api_approve
def api_critical_ack(alert_id: str):
    payload = request.get_json(silent=True) or {}
    try:
        data = acknowledge_critical(alert_id, actor=_actor(), note=payload.get("note"))
        db.session.commit()
        return {"success": True, "data": data}, 200
    except ReportingEngineError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@reporting_engine_bp.route("/patient/<patient_code>/reports", methods=["GET"])
@patient_report_read
def api_patient_reports(patient_code: str):
    return {"success": True, "data": patient_released_reports(patient_code)}, 200


@reporting_engine_bp.route("/report", methods=["GET"])
@report_api_read
def api_report():
    return {"success": True, "data": reporting_engine_report()}, 200


@reporting_engine_bp.route("/doctor-review-report", methods=["GET"])
@report_api_read
def api_doctor_report():
    return {"success": True, "data": doctor_review_report()}, 200


@reporting_engine_bp.route("/security-report", methods=["GET"])
@report_api_read
def api_security_report():
    return {"success": True, "data": report_security_report()}, 200


@reporting_engine_bp.route("/critical-report", methods=["GET"])
@report_api_read
def api_critical_report():
    return {"success": True, "data": critical_result_report()}, 200


@reporting_engine_bp.route("/pdf-report", methods=["GET"])
@report_api_read
def api_pdf_report():
    return {"success": True, "data": production_report_pdf_report()}, 200
