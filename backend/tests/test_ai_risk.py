import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.ai_cds import ClinicalRiskAssessment, CriticalAlertEvent
from app.models.critical_value_rule import CriticalValueRule
from app.services.ai_cds_service import AIRiskService, CriticalDetectionService


def seed_risk_and_critical():
    db.session.add(
        CriticalValueRule(
            rule_code="CRIT-K",
            test_code="K",
            panic_low=2.5,
            panic_high=6.5,
            message_en="Critical potassium",
            status="ACTIVE",
        )
    )
    db.session.commit()


class AIRiskTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        seed_risk_and_critical()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_risk_api(self):
        response = self.client.post(
            "/api/v1/ai/risk",
            json={
                "patient_id": "patient-1",
                "items": [
                    {"test_code": "GLU", "result_value": "140"},
                    {"test_code": "HBA1C", "result_value": "7.2"},
                    {"test_code": "CREA", "result_value": "1.8"},
                    {"test_code": "EGFR", "result_value": "55"},
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["advisory_only"])
        domains = {row["risk_domain"] for row in payload["assessments"]}
        self.assertIn("diabetes", domains)
        self.assertIn("ckd", domains)
        self.assertGreaterEqual(ClinicalRiskAssessment.query.count(), 1)

    def test_risk_service(self):
        result = AIRiskService.assess(
            {
                "items": [
                    {"test_code": "CHOL", "result_value": "240"},
                    {"test_code": "LDL", "result_value": "160"},
                ]
            }
        )
        self.assertTrue(result["advisory_only"])
        self.assertGreaterEqual(len(result["assessments"]), 1)

    def test_critical_results_api(self):
        response = self.client.post(
            "/api/v1/ai/critical-results",
            json={
                "patient_id": "patient-1",
                "items": [
                    {"test_code": "K", "result_value": "7.0", "flag": "HIGH"},
                    {"test_code": "GLU", "result_value": "250", "flag": "HIGH", "previous_value": "100"},
                ],
                "repeated_abnormality": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertGreaterEqual(payload["count"], 1)
        self.assertGreaterEqual(len(payload["notification_events"]), 1)
        self.assertGreaterEqual(CriticalAlertEvent.query.count(), 1)

    def test_critical_service(self):
        result = CriticalDetectionService.detect(
            {
                "items": [
                    {"test_code": "WBC", "result_value": "5", "flag": "HIGH"},
                    {"test_code": "CRP", "result_value": "20", "flag": "HIGH"},
                ]
            }
        )
        self.assertGreaterEqual(result["count"], 1)


if __name__ == "__main__":
    unittest.main()
