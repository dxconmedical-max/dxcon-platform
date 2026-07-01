import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import CDS_PANEL_CBC, CDS_PANEL_CHEMISTRY
from app.extensions.db import db
from app.models.ai_cds import ClinicalGuidelinePack, ClinicalRuleDefinition
from app.models.critical_value_rule import CriticalValueRule
from app.models.reference_range import ReferenceRange
from app.services.ai_cds_service import ClinicalRuleEngineService


def seed_ai_rules():
    db.session.add(
        ReferenceRange(
            test_code="GLU",
            test_name="Glucose",
            sex="ALL",
            age_min=0,
            age_max=120,
            low_value=70,
            high_value=100,
            status="ACTIVE",
        )
    )
    db.session.add(
        ReferenceRange(
            test_code="HGB",
            test_name="Hemoglobin",
            sex="M",
            age_min=18,
            age_max=120,
            low_value=13.5,
            high_value=17.5,
            status="ACTIVE",
        )
    )
    db.session.add(
        CriticalValueRule(
            rule_code="CRIT-GLU",
            test_code="GLU",
            panic_low=40,
            panic_high=500,
            message_en="Critical glucose",
            status="ACTIVE",
        )
    )
    db.session.commit()


class AIRulesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        seed_ai_rules()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_default_guideline_packs(self):
        ClinicalRuleEngineService.ensure_default_packs()
        packs = ClinicalGuidelinePack.query.all()
        self.assertGreaterEqual(len(packs), 9)
        panels = {pack.panel_type for pack in packs}
        self.assertIn(CDS_PANEL_CBC, panels)
        self.assertIn(CDS_PANEL_CHEMISTRY, panels)
        rules = ClinicalRuleDefinition.query.count()
        self.assertGreaterEqual(rules, 9)

    def test_reference_ranges_api(self):
        response = self.client.get("/api/v1/ai/reference-ranges?test_code=GLU")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertGreaterEqual(len(payload["ranges"]), 1)

    def test_age_sex_reference_ranges(self):
        rows = ClinicalRuleEngineService.list_reference_ranges(test_code="HGB", sex="M", age=30)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["test_code"], "HGB")

    def test_delta_check(self):
        delta = ClinicalRuleEngineService.evaluate_delta("patient-1", "GLU", 150, 100, threshold_percent=20)
        self.assertTrue(delta["is_significant"])
        self.assertGreater(delta["delta_percent"], 20)


if __name__ == "__main__":
    unittest.main()
