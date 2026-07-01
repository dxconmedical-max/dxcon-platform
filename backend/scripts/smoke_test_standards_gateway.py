import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.standards.hl7.hl7_builder import build_oru_message
from tests.standards_test_helpers import load_seed_module


def smoke_test():
    with app.app_context():
        db.create_all()
        load_seed_module().seed_all()
        sample = build_oru_message("PAT-001", "ORD-001", "58410-2", "95")
        steps = [
            ("GET code systems", "get", "/api/v1/standards/code-systems", None),
            ("GET codes", "get", "/api/v1/standards/codes?limit=5", None),
            ("GET mappings", "get", "/api/v1/standards/mappings", None),
            ("POST HL7 parse", "post", "/api/v1/standards/hl7/parse", {"message": sample}),
            ("POST HL7 validate", "post", "/api/v1/standards/hl7/validate", {"message": sample}),
            ("POST HL7 build ORU", "post", "/api/v1/standards/hl7/build-oru", {"value": "88"}),
            ("POST FHIR validate", "post", "/api/v1/standards/fhir/validate", {"resourceType": "Patient", "id": "P1", "name": []}),
            ("POST FHIR map result", "post", "/api/v1/standards/fhir/map-result", {"service_code": "SVC-001", "value": "90"}),
            ("POST mapping resolve", "post", "/api/v1/standards/mappings/resolve", {"source_type": "DXCON_SERVICE", "source_code": "SVC-001"}),
            ("GET DICOM studies", "get", "/api/v1/standards/dicom/studies", None),
            ("GET standards home", "get", "/standards", None),
            ("GET standards HL7", "get", "/standards/hl7", None),
        ]
        for label, method, path, payload in steps:
            if method == "get":
                response = client.get(path)
            else:
                response = client.post(path, json=payload or {})
            if response.status_code >= 400:
                print("FAIL:", label, response.status_code, response.get_data(as_text=True)[:200])
                return False
            print("OK:", label, response.status_code)
        return True


app = create_app()
app.config["TESTING"] = True
client = app.test_client()
print("\n=== DXCON STANDARDS GATEWAY SMOKE TEST ===\n")
if not smoke_test():
    print("\nSTANDARDS GATEWAY SMOKE TEST FAILED\n")
    sys.exit(1)
print("\nSTANDARDS GATEWAY SMOKE TEST PASSED\n")
