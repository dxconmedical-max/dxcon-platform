import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.standards.hl7.hl7_builder import build_oru_message
from tests.standards_test_helpers import load_seed_module


def verify_models():
    from app.models.healthcare_standards import (
        DICOMInstanceMetadata,
        DICOMSeriesMetadata,
        DICOMStudyMetadata,
        StandardCode,
        StandardCodeSystem,
        StandardImportBatch,
        StandardMapping,
        StandardValidationLog,
    )

    for model in (
        StandardCodeSystem,
        StandardCode,
        StandardMapping,
        StandardValidationLog,
        StandardImportBatch,
        DICOMStudyMetadata,
        DICOMSeriesMetadata,
        DICOMInstanceMetadata,
    ):
        assert model.__tablename__
        print("OK: model", model.__name__)
    return True


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/standards/code-systems",
        "/api/v1/standards/codes",
        "/api/v1/standards/mappings",
        "/api/v1/standards/mappings/resolve",
        "/api/v1/standards/hl7/parse",
        "/api/v1/standards/hl7/validate",
        "/api/v1/standards/hl7/build-oru",
        "/api/v1/standards/fhir/validate",
        "/api/v1/standards/fhir/map-result",
        "/api/v1/standards/fhir/map-order",
        "/api/v1/standards/dicom/metadata",
        "/api/v1/standards/dicom/studies",
        "/api/v1/standards/dicom/studies/<study_id>",
        "/standards",
        "/standards/hl7",
        "/standards/fhir",
        "/standards/mappings",
        "/standards/dicom",
    ]
    missing = [route for route in required if route not in routes]
    for route in required:
        if route in routes:
            print("OK:", route)
    if missing:
        print("MISSING:", missing)
        return False
    return True


def verify_no_duplicate_routes(app):
    prefixes = ("/api/v1/standards/", "/standards")
    seen = defaultdict(list)
    for rule in app.url_map.iter_rules():
        path = str(rule.rule)
        if not any(path.startswith(prefix) or path == prefix.rstrip("/") for prefix in prefixes):
            continue
        key = (path, tuple(sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})))
        seen[key].append(rule.endpoint)
    duplicates = {key: endpoints for key, endpoints in seen.items() if len(endpoints) > 1}
    if duplicates:
        print("DUPLICATE:", duplicates)
        return False
    print("OK: no duplicate standards routes")
    return True


def _payload(response):
    body = response.get_json() or {}
    if isinstance(body.get("data"), dict) and "success" in body:
        return body["data"]
    return body


def verify_engines(client):
    sample = build_oru_message("PAT-001", "ORD-001", "58410-2", "95")

    parse = client.post("/api/v1/standards/hl7/parse", json={"message": sample})
    if parse.status_code != 200:
        print("FAIL: HL7 parse")
        return False
    print("OK: HL7 parse")

    validate = client.post("/api/v1/standards/hl7/validate", json={"message": sample})
    validate_body = _payload(validate)
    if validate.status_code != 200 or not validate_body.get("valid"):
        print("FAIL: HL7 validate", validate.status_code, validate.get_json())
        return False
    print("OK: HL7 validate")

    build = client.post("/api/v1/standards/hl7/build-oru", json={"value": "99"})
    if build.status_code != 200:
        print("FAIL: HL7 build ORU")
        return False
    print("OK: HL7 build ORU")

    fhir = client.post(
        "/api/v1/standards/fhir/validate",
        json={"resourceType": "DiagnosticReport", "id": "DR-1", "status": "final", "code": {}, "subject": {}},
    )
    fhir_body = _payload(fhir)
    if fhir.status_code != 200 or not fhir_body.get("valid"):
        print("FAIL: FHIR validate")
        return False
    print("OK: FHIR validate")

    map_result = client.post(
        "/api/v1/standards/fhir/map-result",
        json={"patient_id": "PAT-001", "service_code": "SVC-001", "value": "95"},
    )
    if map_result.status_code != 200:
        print("FAIL: FHIR map result")
        return False
    print("OK: FHIR map result")

    resolve = client.post(
        "/api/v1/standards/mappings/resolve",
        json={"source_type": "DXCON_SERVICE", "source_code": "SVC-001", "target_system": "LOINC"},
    )
    resolve_body = _payload(resolve)
    if resolve.status_code != 200 or resolve_body.get("count", 0) < 1:
        print("FAIL: mapping resolve")
        return False
    print("OK: mapping resolve")

    studies = client.get("/api/v1/standards/dicom/studies")
    studies_body = _payload(studies)
    if studies.status_code != 200 or studies_body.get("count", 0) < 1:
        print("FAIL: DICOM list")
        return False
    print("OK: DICOM metadata list")
    return True


app = create_app()
print("\n=== DXCON HEALTHCARE STANDARDS VERIFY ===\n")
errors = 0
print("OK: app creates successfully")
with app.app_context():
    db.create_all()
    load_seed_module().seed_all()
    print("OK: demo seed")
    if not verify_models():
        errors += 1
    if not verify_routes(app):
        errors += 1
    if not verify_no_duplicate_routes(app):
        errors += 1
    client = app.test_client()
    if not verify_engines(client):
        errors += 1
if errors:
    print("\nSTANDARDS GATEWAY VERIFY FAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nSTANDARDS GATEWAY VERIFY PASSED\n")
