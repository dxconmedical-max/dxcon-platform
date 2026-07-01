import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.standards.fhir.fhir_resource import sample_diagnostic_report
from tests.standards_test_helpers import seed_demo_data


class FHIRFoundationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        seed_demo_data()
        self.report = sample_diagnostic_report()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_validate(self):
        response = self.client.post("/api/v1/standards/fhir/validate", json=self.report)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["valid"])

    def test_map_result(self):
        response = self.client.post(
            "/api/v1/standards/fhir/map-result",
            json={"patient_id": "PAT-001", "order_id": "ORD-001", "service_code": "SVC-001", "value": "95", "unit": "mg/dL"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["diagnostic_report"]["resourceType"], "DiagnosticReport")
        self.assertEqual(payload["observation"]["resourceType"], "Observation")

    def test_map_order(self):
        response = self.client.post(
            "/api/v1/standards/fhir/map-order",
            json={"patient_id": "PAT-001", "order_id": "ORD-001", "service_code": "SVC-001"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["resource"]["resourceType"], "ServiceRequest")


if __name__ == "__main__":
    unittest.main()
