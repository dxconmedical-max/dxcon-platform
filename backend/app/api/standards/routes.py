from flask import Blueprint, request

from app.services.healthcare_standards_service import (
    CodeMappingService,
    DICOMMetadataService,
    FHIRStandardsService,
    HealthcareStandardsService,
    HL7StandardsService,
    StandardsError,
)


def _error(exc):
    return {"error": exc.message}, exc.status_code


standards_bp = Blueprint("healthcare_standards", __name__, url_prefix="/api/v1/standards")


@standards_bp.route("/code-systems", methods=["GET"])
def list_code_systems():
    return HealthcareStandardsService.list_code_systems()


@standards_bp.route("/codes", methods=["GET"])
def list_codes():
    return HealthcareStandardsService.list_codes(
        system_code=request.args.get("system_code"),
        limit=int(request.args.get("limit") or 100),
    )


@standards_bp.route("/mappings", methods=["GET"])
def list_mappings():
    return CodeMappingService.list_mappings(
        source_type=request.args.get("source_type"),
        target_system=request.args.get("target_system"),
    )


@standards_bp.route("/mappings", methods=["POST"])
def create_mapping():
    try:
        return CodeMappingService.create_mapping(request.get_json(silent=True) or {}), 201
    except StandardsError as exc:
        return _error(exc)


@standards_bp.route("/mappings/resolve", methods=["POST"])
def resolve_mapping():
    try:
        return CodeMappingService.resolve(request.get_json(silent=True) or {})
    except StandardsError as exc:
        return _error(exc)


@standards_bp.route("/hl7/parse", methods=["POST"])
def hl7_parse():
    data = request.get_json(silent=True) or {}
    raw = data.get("message") or data.get("raw")
    if not raw:
        return {"error": "message is required"}, 400
    try:
        return HL7StandardsService.parse(raw)
    except StandardsError as exc:
        return _error(exc)


@standards_bp.route("/hl7/validate", methods=["POST"])
def hl7_validate():
    data = request.get_json(silent=True) or {}
    raw = data.get("message") or data.get("raw")
    if not raw:
        return {"error": "message is required"}, 400
    return HL7StandardsService.validate(raw)


@standards_bp.route("/hl7/build-oru", methods=["POST"])
def hl7_build_oru():
    return HL7StandardsService.build_oru(request.get_json(silent=True) or {})


@standards_bp.route("/fhir/validate", methods=["POST"])
def fhir_validate():
    return FHIRStandardsService.validate(request.get_json(silent=True) or {})


@standards_bp.route("/fhir/map-result", methods=["POST"])
def fhir_map_result():
    return FHIRStandardsService.map_result(request.get_json(silent=True) or {})


@standards_bp.route("/fhir/map-order", methods=["POST"])
def fhir_map_order():
    return FHIRStandardsService.map_order(request.get_json(silent=True) or {})


@standards_bp.route("/dicom/metadata", methods=["POST"])
def dicom_metadata_save():
    try:
        return DICOMMetadataService.save_metadata(request.get_json(silent=True) or {}), 201
    except StandardsError as exc:
        return _error(exc)


@standards_bp.route("/dicom/studies", methods=["GET"])
def dicom_studies():
    return DICOMMetadataService.list_studies()


@standards_bp.route("/dicom/studies/<study_id>", methods=["GET"])
def dicom_study_detail(study_id):
    try:
        return DICOMMetadataService.get_study(study_id)
    except StandardsError as exc:
        return _error(exc)
