import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from tests.standards_test_helpers import seed_demo_data


class CodeMappingTestCase(unittest.TestCase):
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

    def test_list_codes_and_mappings(self):
        codes = self.client.get("/api/v1/standards/codes?system_code=LOINC&limit=10")
        self.assertEqual(codes.status_code, 200)
        self.assertGreaterEqual(codes.get_json()["count"], 10)

        mappings = self.client.get("/api/v1/standards/mappings")
        self.assertEqual(mappings.status_code, 200)
        self.assertGreaterEqual(mappings.get_json()["count"], 50)

    def test_resolve_mapping(self):
        response = self.client.post(
            "/api/v1/standards/mappings/resolve",
            json={"source_type": "DXCON_SERVICE", "source_code": "SVC-001", "target_system": "LOINC"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.get_json()["count"], 1)

    def test_create_mapping(self):
        response = self.client.post(
            "/api/v1/standards/mappings",
            json={
                "source_type": "DXCON_CONCEPT",
                "source_code": "CONCEPT-001",
                "target_system": "SNOMED_CT",
                "target_code": "SCT-0001",
            },
        )
        self.assertEqual(response.status_code, 201)


if __name__ == "__main__":
    unittest.main()
