import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.standards.hl7.hl7_builder import build_oru_message
from app.standards.hl7.hl7_parser import parse_hl7
from tests.standards_test_helpers import seed_demo_data


class HL7FoundationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        seed_demo_data()
        self.sample = build_oru_message("PAT-001", "ORD-001", "58410-2", "95")

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_parse(self):
        parsed = parse_hl7(self.sample)
        self.assertEqual(parsed.message_type, "ORU")
        self.assertIn("OBX", parsed.segments)

    def test_parse_api(self):
        response = self.client.post("/api/v1/standards/hl7/parse", json={"message": self.sample})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["message_type"], "ORU")

    def test_validate_and_build_oru(self):
        validate = self.client.post("/api/v1/standards/hl7/validate", json={"message": self.sample})
        self.assertEqual(validate.status_code, 200)
        self.assertTrue(validate.get_json()["valid"])

        build = self.client.post("/api/v1/standards/hl7/build-oru", json={"patient_id": "PAT-002", "value": "101"})
        self.assertEqual(build.status_code, 200)
        self.assertIn("message", build.get_json())


if __name__ == "__main__":
    unittest.main()
