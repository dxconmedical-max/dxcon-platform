"""Healthcare Standards Advanced API routes — Phase 4 Sprint 4.4."""

from __future__ import annotations

from flask import Blueprint, request, session

from app.services.standards_advanced_service import (
    StandardsAdvancedError,
    dashboard_payload,
    export_oru_result,
    import_adt_patient,
    import_orm_order,
    list_audit_log,
    map_fhir_diagnostic_report,
    map_fhir_observation,
    map_fhir_patient,
    sandbox_messages,
    validate_icd10,
    validate_loinc,
)

standards_advanced_bp = Blueprint(
    "standards_advanced_api",
    __name__,
    url_prefix="/api/v1/standards-advanced",
)


def _actor() -> str | None:
    return session.get("email")


@standards_advanced_bp.route("/dashboard", methods=["GET"])
def standards_advanced_dashboard_api():
    return dashboard_payload()


@standards_advanced_bp.route("/hl7/oru/export", methods=["POST"])
def standards_advanced_oru_export_api():
    data = request.get_json(silent=True) or {}
    try:
        return export_oru_result(data, actor=_actor())
    except StandardsAdvancedError as exc:
        return {"error": exc.message}, exc.status_code


@standards_advanced_bp.route("/hl7/orm/import", methods=["POST"])
def standards_advanced_orm_import_api():
    data = request.get_json(silent=True) or {}
    raw = data.get("message") or data.get("raw")
    if not raw:
        return {"error": "message is required"}, 400
    try:
        return import_orm_order(raw, actor=_actor())
    except StandardsAdvancedError as exc:
        return {"error": exc.message}, exc.status_code


@standards_advanced_bp.route("/hl7/adt/import", methods=["POST"])
def standards_advanced_adt_import_api():
    data = request.get_json(silent=True) or {}
    raw = data.get("message") or data.get("raw")
    if not raw:
        return {"error": "message is required"}, 400
    try:
        return import_adt_patient(raw, actor=_actor())
    except StandardsAdvancedError as exc:
        return {"error": exc.message}, exc.status_code


@standards_advanced_bp.route("/fhir/patient/map", methods=["POST"])
def standards_advanced_fhir_patient_api():
    try:
        return map_fhir_patient(request.get_json(silent=True) or {}, actor=_actor())
    except StandardsAdvancedError as exc:
        return {"error": exc.message}, exc.status_code


@standards_advanced_bp.route("/fhir/diagnostic-report/map", methods=["POST"])
def standards_advanced_fhir_diagnostic_api():
    try:
        return map_fhir_diagnostic_report(request.get_json(silent=True) or {}, actor=_actor())
    except StandardsAdvancedError as exc:
        return {"error": exc.message}, exc.status_code


@standards_advanced_bp.route("/fhir/observation/map", methods=["POST"])
def standards_advanced_fhir_observation_api():
    try:
        return map_fhir_observation(request.get_json(silent=True) or {}, actor=_actor())
    except StandardsAdvancedError as exc:
        return {"error": exc.message}, exc.status_code


@standards_advanced_bp.route("/loinc/validate", methods=["POST"])
def standards_advanced_loinc_api():
    data = request.get_json(silent=True) or {}
    try:
        return validate_loinc(data.get("code", ""))
    except StandardsAdvancedError as exc:
        return {"error": exc.message}, exc.status_code


@standards_advanced_bp.route("/icd10/validate", methods=["POST"])
def standards_advanced_icd10_api():
    data = request.get_json(silent=True) or {}
    try:
        return validate_icd10(data.get("code", ""))
    except StandardsAdvancedError as exc:
        return {"error": exc.message}, exc.status_code


@standards_advanced_bp.route("/audit", methods=["GET"])
def standards_advanced_audit_api():
    page = request.args.get("page", 1)
    page_size = request.args.get("page_size", 50)
    return list_audit_log(page=page, page_size=page_size)


@standards_advanced_bp.route("/sandbox/messages", methods=["GET"])
def standards_advanced_sandbox_api():
    return sandbox_messages()
