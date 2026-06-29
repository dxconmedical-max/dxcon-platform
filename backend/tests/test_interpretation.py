import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
    INTERPRETATION_FLAG_CRITICAL,
    INTERPRETATION_FLAG_HIGH,
    MAPPING_ACTIVE,
    PARTNER_ACTIVE,
)
from app.extensions.db import db
from app.models.company import Company
from app.models.interpretation_result import InterpretationResult
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.services.interpretation_engine_service import (
    CriticalValueService,
    InterpretationEngine,
    ReferenceRangeService,
)
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_workflow_service import OrderWorkflowService
from app.services.result_gateway_service import ResultUploadService, ResultValidationService
from app.services.scheduling import SchedulingService
from app.services.slot_generation import SlotGenerationService
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from scripts.seed_interpretation_demo import seed_interpretation_demo


class InterpretationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        db.session.add(Company(company_code="DX", company_name="DxCon", tax_code="01"))
        cat = DiagnosticCategory(category_code="BIO", name="Bio", is_active=True)
        db.session.add(cat)
        db.session.flush()
        svc = DiagnosticService(service_code="GLU", name="Glucose", category_id=cat.id, is_active=True)
        db.session.add(svc)
        self.partner = Partner(
            partner_code="PTR-INT-001",
            partner_type="LABORATORY",
            legal_name="Interpretation Lab",
            display_name="Interpretation Lab",
            status=PARTNER_ACTIVE,
        )
        db.session.add(self.partner)
        db.session.flush()
        self.mapping = PartnerServiceMapping(
            partner_id=self.partner.id,
            diagnostic_service_id=svc.id,
            partner_service_code="INT-GLU",
            partner_service_name="Glucose",
            price=120000,
            status=MAPPING_ACTIVE,
        )
        db.session.add(self.mapping)
        db.session.commit()
        SlotGenerationService.generate_partner_daily_slots(self.partner.id, days=2)
        seed_interpretation_demo()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _lab_result(self, value="7.2", test_code="GLU"):
        slot = SchedulingService.list_available_slots(self.partner.id)[0]
        booking = MarketplaceBookingService.create_booking(
            {
                "partner_service_mapping_id": self.mapping.id,
                "patient_name": "Interpret Patient",
                "patient_phone": "0909000444",
                "requested_date": slot.slot_date,
            }
        )
        order = OrderWorkflowService.create_from_booking(booking.id)
        result = ResultUploadService.create_manual(
            {
                "medical_order_id": order.id,
                "items": [
                    {
                        "test_code": test_code,
                        "test_name": "Glucose" if test_code == "GLU" else "Potassium",
                        "result_value": value,
                        "unit": "mmol/L",
                    }
                ],
            }
        )
        ResultValidationService.validate(result.id)
        return result

    def test_interpretation_apis(self):
        lab_result = self._lab_result(value="7.2")
        rules = self.client.get("/api/v1/interpretation/rules")
        self.assertEqual(rules.status_code, 200)
        self.assertGreaterEqual(rules.get_json()["rules_count"], 1)

        ranges = self.client.get("/api/v1/reference-ranges?test_code=GLU")
        self.assertEqual(ranges.status_code, 200)
        self.assertGreaterEqual(ranges.get_json()["count"], 1)

        run = self.client.post(
            "/api/v1/interpretation/run",
            json={"lab_result_id": lab_result.id, "patient_age": 35, "patient_sex": "F"},
        )
        self.assertEqual(run.status_code, 201)
        payload = run.get_json()
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["interpretations"][0]["flag"], INTERPRETATION_FLAG_HIGH)

        detail = self.client.get(f"/api/v1/interpretation/{lab_result.id}?language=vi")
        self.assertEqual(detail.status_code, 200)
        self.assertGreaterEqual(detail.get_json()["count"], 1)
        self.assertIn("interpretation", detail.get_json()["interpretations"][0])

    def test_interpretation_services(self):
        lab_result = self._lab_result(value="2.1", test_code="K")
        critical = CriticalValueService.evaluate("K", "2.1")
        self.assertTrue(critical["is_critical"])

        reference = ReferenceRangeService.resolve("GLU", age=35, sex="F")
        self.assertIsNotNone(reference)

        rows = InterpretationEngine.run(lab_result.id, patient_age=40, patient_sex="M")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].flag, INTERPRETATION_FLAG_CRITICAL)
        self.assertIsNotNone(InterpretationResult.query.get(rows[0].id))

    def test_interpretation_web_routes(self):
        routes = {str(r) for r in self.app.url_map.iter_rules()}
        for route in ["/interpretation", "/reference-ranges", "/critical-values"]:
            self.assertIn(route, routes)


if __name__ == "__main__":
    unittest.main()
