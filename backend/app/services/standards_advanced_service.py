"""Healthcare Standards Advanced business logic for Phase 4 Sprint 4.4."""

from __future__ import annotations

from typing import Any

from app.models.healthcare_standards import StandardValidationLog
from app.services.healthcare_standards_service import (
    CodeMappingService,
    FHIRStandardsService,
    HL7StandardsService,
    HealthcareStandardsService,
    StandardsError,
)
from app.standards.fhir.fhir_mapper import map_observation_to_fhir, map_patient_to_fhir
from app.standards.hl7.hl7_builder import build_adt_message, build_orm_message, build_oru_message
from app.standards.normalizer import normalize_hl7_payload
from app.standards.validators import log_validation, validate_code_reference

STANDARDS_ROLES = ("SUPER_ADMIN", "ADMIN")

FEATURES = (
    "HL7 ORU Result Export",
    "HL7 ORM Order Import",
    "HL7 ADT Patient Import",
    "FHIR Patient Mapping",
    "FHIR DiagnosticReport Mapping",
    "FHIR Observation Mapping",
    "LOINC Mapping Validation",
    "ICD-10 Mapping Validation",
    "Standards Audit Log",
    "Integration Sandbox Messages",
    "Verification Report",
)


class StandardsAdvancedError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def ensure_standards() -> dict[str, Any]:
    from app.models.healthcare_standards import StandardCodeSystem

    if not StandardCodeSystem.query.first():
        try:
            from scripts.seed_standards_demo import seed_all

            seed_all()
        except Exception:
            HealthcareStandardsService.list_code_systems()
    return {"ready": True}


def dashboard_payload() -> dict[str, Any]:
    ensure_standards()
    systems = HealthcareStandardsService.list_code_systems()
    mappings = CodeMappingService.list_mappings()
    audit = list_audit_log(page_size=5)
    return {
        "platform": "Healthcare Standards Advanced",
        "phase": "4.4",
        "sprint": "Healthcare Standards Advanced",
        "status": "OK",
        "summary": {
            "code_systems": systems["count"],
            "mappings": mappings["count"],
            "audit_entries": audit["count"],
            "hl7_message_types": ["ORU", "ORM", "ADT"],
            "fhir_resources": ["Patient", "Observation", "DiagnosticReport"],
        },
        "features": list(FEATURES),
    }


def export_oru_result(data: dict[str, Any], *, actor: str | None = None) -> dict[str, Any]:
    ensure_standards()
    payload = data or {}
    try:
        result = HL7StandardsService.build_oru(payload)
    except StandardsError as exc:
        raise StandardsAdvancedError(exc.message, exc.status_code) from exc
    audit = log_validation("HL7_V2", "ORU", "EXPORTED", {"actor": actor or "SYSTEM", "order_id": payload.get("order_id")})
    return {"message_type": "ORU", "export": result, "audit_id": audit["id"]}


def import_orm_order(raw_message: str, *, actor: str | None = None) -> dict[str, Any]:
    ensure_standards()
    if not raw_message:
        raise StandardsAdvancedError("message is required", 400)
    try:
        parsed = HL7StandardsService.parse(raw_message)
    except StandardsError as exc:
        raise StandardsAdvancedError(exc.message, exc.status_code) from exc
    if parsed.get("message_type") != "ORM":
        raise StandardsAdvancedError("Expected ORM message type", 400)
    normalized = normalize_hl7_payload("ORM", parsed.get("segments") or {})
    audit = log_validation("HL7_V2", "ORM", "IMPORTED", {"actor": actor or "SYSTEM", "order": normalized.get("order")})
    return {"message_type": "ORM", "parsed": parsed, "normalized": normalized, "audit_id": audit["id"]}


def import_adt_patient(raw_message: str, *, actor: str | None = None) -> dict[str, Any]:
    ensure_standards()
    if not raw_message:
        raise StandardsAdvancedError("message is required", 400)
    try:
        parsed = HL7StandardsService.parse(raw_message)
    except StandardsError as exc:
        raise StandardsAdvancedError(exc.message, exc.status_code) from exc
    if parsed.get("message_type") != "ADT":
        raise StandardsAdvancedError("Expected ADT message type", 400)
    normalized = normalize_hl7_payload("ADT", parsed.get("segments") or {})
    audit = log_validation("HL7_V2", "ADT", "IMPORTED", {"actor": actor or "SYSTEM", "patient": normalized.get("patient")})
    return {"message_type": "ADT", "parsed": parsed, "normalized": normalized, "audit_id": audit["id"]}


def map_fhir_patient(data: dict[str, Any], *, actor: str | None = None) -> dict[str, Any]:
    ensure_standards()
    mapped = map_patient_to_fhir(data)
    validation = FHIRStandardsService.validate(mapped["resource"])
    audit = log_validation(
        "FHIR_R4",
        "Patient",
        "MAPPED" if validation.get("valid") else "INVALID",
        {"actor": actor or "SYSTEM"},
    )
    mapped["validation"] = validation
    mapped["audit_id"] = audit["id"]
    return mapped


def map_fhir_diagnostic_report(data: dict[str, Any], *, actor: str | None = None) -> dict[str, Any]:
    ensure_standards()
    mapped = FHIRStandardsService.map_result(data)
    validation = FHIRStandardsService.validate(mapped.get("diagnostic_report") or {})
    audit = log_validation(
        "FHIR_R4",
        "DiagnosticReport",
        "MAPPED" if validation.get("valid") else "INVALID",
        {"actor": actor or "SYSTEM"},
    )
    mapped["validation"] = validation
    mapped["audit_id"] = audit["id"]
    return mapped


def map_fhir_observation(data: dict[str, Any], *, actor: str | None = None) -> dict[str, Any]:
    ensure_standards()
    mapped = map_observation_to_fhir(data)
    validation = FHIRStandardsService.validate(mapped.get("observation") or {})
    audit = log_validation(
        "FHIR_R4",
        "Observation",
        "MAPPED" if validation.get("valid") else "INVALID",
        {"actor": actor or "SYSTEM"},
    )
    mapped["validation"] = validation
    mapped["audit_id"] = audit["id"]
    return mapped


def validate_loinc(code: str) -> dict[str, Any]:
    ensure_standards()
    if not code:
        raise StandardsAdvancedError("code is required", 400)
    result = validate_code_reference("LOINC", code)
    log_validation("LOINC", "Code", "VALID" if result["valid"] else "INVALID", result)
    return {"system": "LOINC", "code": code, **result}


def validate_icd10(code: str) -> dict[str, Any]:
    ensure_standards()
    if not code:
        raise StandardsAdvancedError("code is required", 400)
    result = validate_code_reference("ICD10", code)
    log_validation("ICD10", "Code", "VALID" if result["valid"] else "INVALID", result)
    return {"system": "ICD10", "code": code, **result}


def list_audit_log(*, page: int = 1, page_size: int = 50) -> dict[str, Any]:
    page = max(int(page or 1), 1)
    page_size = min(max(int(page_size or 50), 1), 200)
    query = StandardValidationLog.query
    total = query.count()
    rows = (
        query.order_by(StandardValidationLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"count": total, "entries": [row.to_dict() for row in rows]}


def sandbox_messages() -> dict[str, Any]:
    ensure_standards()
    oru = build_oru_message("PAT-SANDBOX", "ORD-SANDBOX", "58410-2", "98", "mg/dL")
    orm = build_orm_message("PAT-SANDBOX", "ORD-SANDBOX", "58410-2")
    adt = build_adt_message("PAT-SANDBOX", "Sandbox^Patient")
    patient = map_patient_to_fhir({"patient_id": "PAT-SANDBOX", "name": "Sandbox^Patient", "gender": "M", "birth_date": "1980-01-01"})
    observation = map_observation_to_fhir(
        {
            "patient_id": "PAT-SANDBOX",
            "order_id": "ORD-SANDBOX",
            "value": "98",
            "unit": "mg/dL",
            "reference_range": "70-110",
            "service_code": "CBC",
        }
    )
    diagnostic = FHIRStandardsService.map_result(
        {
            "patient_id": "PAT-SANDBOX",
            "order_id": "ORD-SANDBOX",
            "value": "98",
            "unit": "mg/dL",
            "reference_range": "70-110",
            "service_code": "CBC",
        }
    )
    return {
        "sandbox": True,
        "hl7": {"oru": oru, "orm": orm, "adt": adt},
        "fhir": {
            "patient": patient["resource"],
            "observation": observation["observation"],
            "diagnostic_report": diagnostic["diagnostic_report"],
        },
    }
