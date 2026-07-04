"""Healthcare Standards Advanced web routes — Phase 4 Sprint 4.4."""

from __future__ import annotations

import json

from flask import Blueprint, request, session

from app.services.standards_advanced_service import (
    STANDARDS_ROLES,
    StandardsAdvancedError,
    export_oru_result,
    import_adt_patient,
    import_orm_order,
    map_fhir_diagnostic_report,
    map_fhir_observation,
    map_fhir_patient,
    sandbox_messages,
    validate_icd10,
    validate_loinc,
)
from app.utils.auth import role_required
from app.web.standards_advanced_lib import (
    build_audit_body,
    build_code_form,
    build_dashboard_body,
    build_json_form,
    build_message_form,
    build_sandbox_body,
    render_standards_page,
)

standards_advanced_web_bp = Blueprint("standards_advanced_web", __name__)


def _actor() -> str | None:
    return session.get("email")


@standards_advanced_web_bp.route("/standards-advanced")
@role_required(*STANDARDS_ROLES)
def standards_advanced_dashboard():
    return render_standards_page("Healthcare Standards Advanced", build_dashboard_body())


@standards_advanced_web_bp.route("/standards-advanced/audit")
@role_required(*STANDARDS_ROLES)
def standards_advanced_audit():
    return render_standards_page("Standards Audit Log", build_audit_body())


@standards_advanced_web_bp.route("/standards-advanced/sandbox")
@role_required(*STANDARDS_ROLES)
def standards_advanced_sandbox():
    return render_standards_page("Sandbox Messages", build_sandbox_body())


@standards_advanced_web_bp.route("/standards-advanced/hl7-oru", methods=["GET", "POST"])
@role_required(*STANDARDS_ROLES)
def standards_advanced_hl7_oru():
    default = '{"patient_id":"PAT-001","order_id":"ORD-001","observation_code":"58410-2","value":"95","unit":"mg/dL"}'
    if request.method == "GET":
        return render_standards_page("HL7 ORU Export", build_json_form(title="HL7 ORU Export", subtitle="Export lab result as HL7 ORU^R01.", action="", default=default))
    try:
        result = export_oru_result(json.loads(request.form.get("payload", "{}")), actor=_actor())
        return render_standards_page("HL7 ORU Export", build_json_form(title="HL7 ORU Export", subtitle="Export lab result as HL7 ORU^R01.", action="", default=default, result=result))
    except (json.JSONDecodeError, StandardsAdvancedError) as exc:
        message = "Invalid JSON payload." if isinstance(exc, json.JSONDecodeError) else exc.message
        return render_standards_page("HL7 ORU Export", build_json_form(title="HL7 ORU Export", subtitle="Export lab result as HL7 ORU^R01.", action="", default=default, error=message))


@standards_advanced_web_bp.route("/standards-advanced/hl7-orm", methods=["GET", "POST"])
@role_required(*STANDARDS_ROLES)
def standards_advanced_hl7_orm():
    default = sandbox_messages()["hl7"]["orm"]
    if request.method == "GET":
        return render_standards_page("HL7 ORM Import", build_message_form(title="HL7 ORM Import", subtitle="Import lab order from HL7 ORM^O01.", default=default))
    try:
        result = import_orm_order(request.form.get("message", ""), actor=_actor())
        return render_standards_page("HL7 ORM Import", build_message_form(title="HL7 ORM Import", subtitle="Import lab order from HL7 ORM^O01.", default=default, result=result))
    except StandardsAdvancedError as exc:
        return render_standards_page("HL7 ORM Import", build_message_form(title="HL7 ORM Import", subtitle="Import lab order from HL7 ORM^O01.", default=default, error=exc.message))


@standards_advanced_web_bp.route("/standards-advanced/hl7-adt", methods=["GET", "POST"])
@role_required(*STANDARDS_ROLES)
def standards_advanced_hl7_adt():
    default = sandbox_messages()["hl7"]["adt"]
    if request.method == "GET":
        return render_standards_page("HL7 ADT Import", build_message_form(title="HL7 ADT Import", subtitle="Import patient demographics from HL7 ADT.", default=default))
    try:
        result = import_adt_patient(request.form.get("message", ""), actor=_actor())
        return render_standards_page("HL7 ADT Import", build_message_form(title="HL7 ADT Import", subtitle="Import patient demographics from HL7 ADT.", default=default, result=result))
    except StandardsAdvancedError as exc:
        return render_standards_page("HL7 ADT Import", build_message_form(title="HL7 ADT Import", subtitle="Import patient demographics from HL7 ADT.", default=default, error=exc.message))


@standards_advanced_web_bp.route("/standards-advanced/fhir-patient", methods=["GET", "POST"])
@role_required(*STANDARDS_ROLES)
def standards_advanced_fhir_patient():
    default = '{"patient_id":"PAT-001","name":"Demo^Patient","gender":"M","birth_date":"1980-01-01"}'
    if request.method == "GET":
        return render_standards_page("FHIR Patient", build_json_form(title="FHIR Patient Mapping", subtitle="Map internal patient to FHIR R4 Patient.", action="", default=default))
    try:
        result = map_fhir_patient(json.loads(request.form.get("payload", "{}")), actor=_actor())
        return render_standards_page("FHIR Patient", build_json_form(title="FHIR Patient Mapping", subtitle="Map internal patient to FHIR R4 Patient.", action="", default=default, result=result))
    except (json.JSONDecodeError, StandardsAdvancedError) as exc:
        message = "Invalid JSON payload." if isinstance(exc, json.JSONDecodeError) else exc.message
        return render_standards_page("FHIR Patient", build_json_form(title="FHIR Patient Mapping", subtitle="Map internal patient to FHIR R4 Patient.", action="", default=default, error=message))


@standards_advanced_web_bp.route("/standards-advanced/fhir-diagnostic", methods=["GET", "POST"])
@role_required(*STANDARDS_ROLES)
def standards_advanced_fhir_diagnostic():
    default = '{"patient_id":"PAT-001","order_id":"ORD-001","value":"95","unit":"mg/dL","reference_range":"70-110","service_code":"SVC-001"}'
    if request.method == "GET":
        return render_standards_page("FHIR DiagnosticReport", build_json_form(title="FHIR DiagnosticReport Mapping", subtitle="Map lab result to FHIR DiagnosticReport.", action="", default=default))
    try:
        result = map_fhir_diagnostic_report(json.loads(request.form.get("payload", "{}")), actor=_actor())
        return render_standards_page("FHIR DiagnosticReport", build_json_form(title="FHIR DiagnosticReport Mapping", subtitle="Map lab result to FHIR DiagnosticReport.", action="", default=default, result=result))
    except (json.JSONDecodeError, StandardsAdvancedError) as exc:
        message = "Invalid JSON payload." if isinstance(exc, json.JSONDecodeError) else exc.message
        return render_standards_page("FHIR DiagnosticReport", build_json_form(title="FHIR DiagnosticReport Mapping", subtitle="Map lab result to FHIR DiagnosticReport.", action="", default=default, error=message))


@standards_advanced_web_bp.route("/standards-advanced/fhir-observation", methods=["GET", "POST"])
@role_required(*STANDARDS_ROLES)
def standards_advanced_fhir_observation():
    default = '{"patient_id":"PAT-001","order_id":"ORD-001","value":"95","unit":"mg/dL","reference_range":"70-110","service_code":"SVC-001"}'
    if request.method == "GET":
        return render_standards_page("FHIR Observation", build_json_form(title="FHIR Observation Mapping", subtitle="Map lab result value to FHIR Observation.", action="", default=default))
    try:
        result = map_fhir_observation(json.loads(request.form.get("payload", "{}")), actor=_actor())
        return render_standards_page("FHIR Observation", build_json_form(title="FHIR Observation Mapping", subtitle="Map lab result value to FHIR Observation.", action="", default=default, result=result))
    except (json.JSONDecodeError, StandardsAdvancedError) as exc:
        message = "Invalid JSON payload." if isinstance(exc, json.JSONDecodeError) else exc.message
        return render_standards_page("FHIR Observation", build_json_form(title="FHIR Observation Mapping", subtitle="Map lab result value to FHIR Observation.", action="", default=default, error=message))


@standards_advanced_web_bp.route("/standards-advanced/loinc", methods=["GET", "POST"])
@role_required(*STANDARDS_ROLES)
def standards_advanced_loinc():
    if request.method == "GET":
        return render_standards_page("LOINC Validation", build_code_form(title="LOINC Mapping Validation", subtitle="Validate LOINC code against seeded registry.", field_name="code", default="LNC-0001"))
    try:
        result = validate_loinc(request.form.get("code", "").strip())
        return render_standards_page("LOINC Validation", build_code_form(title="LOINC Mapping Validation", subtitle="Validate LOINC code against seeded registry.", field_name="code", default=request.form.get("code", ""), result=result))
    except StandardsAdvancedError as exc:
        return render_standards_page("LOINC Validation", build_code_form(title="LOINC Mapping Validation", subtitle="Validate LOINC code against seeded registry.", field_name="code", default=request.form.get("code", ""), error=exc.message))


@standards_advanced_web_bp.route("/standards-advanced/icd10", methods=["GET", "POST"])
@role_required(*STANDARDS_ROLES)
def standards_advanced_icd10():
    if request.method == "GET":
        return render_standards_page("ICD-10 Validation", build_code_form(title="ICD-10 Mapping Validation", subtitle="Validate ICD-10 code against seeded registry.", field_name="code", default="I10-0001"))
    try:
        result = validate_icd10(request.form.get("code", "").strip())
        return render_standards_page("ICD-10 Validation", build_code_form(title="ICD-10 Mapping Validation", subtitle="Validate ICD-10 code against seeded registry.", field_name="code", default=request.form.get("code", ""), result=result))
    except StandardsAdvancedError as exc:
        return render_standards_page("ICD-10 Validation", build_code_form(title="ICD-10 Mapping Validation", subtitle="Validate ICD-10 code against seeded registry.", field_name="code", default=request.form.get("code", ""), error=exc.message))
