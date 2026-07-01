import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import CDS_PANEL_CBC, CDS_PANEL_LIVER
from app.extensions.db import db
from app.models.reference_range import ReferenceRange
from app.services.ai_cds_service import AIInterpretationService, AIRecommendationService


def seed_interpretation():
    ranges = [
        ("WBC", "White Blood Cell", 4.0, 11.0),
        ("ALT", "Alanine Aminotransferase", 7, 56),
        ("GLU", "Glucose", 70, 100),
    ]
    for code, name, low, high in ranges:
        db.session.add(
            ReferenceRange(
                test_code=code,
                test_name=name,
                sex="ALL",
                age_min=0,
                age_max=120,
                low_value=low,
                high_value=high,
                status="ACTIVE",
            )
        )
    db.session.commit()


class AIInterpretationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        seed_interpretation()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_interpret_api(self):
        response = self.client.post(
            "/api/v1/ai/interpret",
            json={
                "patient_age": 45,
                "patient_sex": "M",
                "items": [
                    {"test_code": "WBC", "test_name": "WBC", "result_value": "14.5", "unit": "10^9/L"},
                    {"test_code": "ALT", "test_name": "ALT", "result_value": "80", "unit": "U/L"},
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["count"], 2)
        self.assertTrue(payload["advisory_only"])
        panels = {item["panel_type"] for item in payload["interpretations"]}
        self.assertIn(CDS_PANEL_CBC, panels)
        self.assertIn(CDS_PANEL_LIVER, panels)
        abnormal = [item for item in payload["interpretations"] if item["abnormal_findings"]]
        self.assertGreaterEqual(len(abnormal), 1)
        for item in payload["interpretations"]:
            self.assertIn("confidence_score", item)
            self.assertIn("supporting_rules", item)

    def test_interpret_service(self):
        result = AIInterpretationService.interpret_payload(
            {
                "items": [{"test_code": "GLU", "test_name": "Glucose", "result_value": "180"}],
            }
        )
        self.assertGreaterEqual(result["count"], 1)

    def test_recommend_api(self):
        response = self.client.post(
            "/api/v1/ai/recommend",
            json={
                "items": [{"test_code": "ALT", "test_name": "ALT", "result_value": "120", "unit": "U/L"}],
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["advisory_only"])
        self.assertGreaterEqual(payload["count"], 1)
        self.assertTrue(all(rec["advisory_only"] for rec in payload["recommendations"]))

    def test_recommend_service(self):
        result = AIRecommendationService.generate(
            {"items": [{"test_code": "GLU", "test_name": "Glucose", "result_value": "200"}]}
        )
        self.assertTrue(result["advisory_only"])


if __name__ == "__main__":
    unittest.main()
