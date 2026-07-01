import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.standards.registry import StandardsRegistry
from tests.standards_test_helpers import seed_demo_data


class StandardsCoreTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        seed_demo_data()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_supported_code_systems(self):
        systems = StandardsRegistry.list_code_systems()
        self.assertEqual(len(systems), 6)
        codes = {item["system_code"] for item in systems}
        self.assertTrue({"LOINC", "ICD10", "SNOMED_CT", "FHIR_R4", "HL7_V2", "DICOM"}.issubset(codes))

    def test_code_systems_api(self):
        response = self.client.get("/api/v1/standards/code-systems")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.get_json()["count"], 6)

    def test_web_routes(self):
        for path in ("/standards", "/standards/hl7", "/standards/fhir", "/standards/mappings", "/standards/dicom"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)


if __name__ == "__main__":
    unittest.main()
