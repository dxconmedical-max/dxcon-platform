import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
    LAB_RESULT_APPROVED,
    LAB_RESULT_DRAFT,
    LAB_RESULT_IN_REVIEW,
    LAB_RESULT_RELEASED,
    LAB_RESULT_VALIDATED,
    MAPPING_ACTIVE,
    PARTNER_ACTIVE,
)
from app.extensions.db import db
from app.models.company import Company
from app.models.lab_result import LabResult
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.models.result_release import ResultRelease
from app.models.result_timeline import ResultTimeline
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_workflow_service import OrderWorkflowService
from app.services.result_gateway_service import (
    ResultApprovalService,
    ResultGatewayBase,
    ResultReleaseService,
    ResultReviewService,
    ResultUploadService,
)
from app.services.scheduling import SchedulingService
from app.services.slot_generation import SlotGenerationService
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService


class ResultsGatewayTestCase(unittest.TestCase):
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
            partner_code="PTR-RG-001",
            partner_type="LABORATORY",
            legal_name="Result Lab",
            display_name="Result Lab",
            status=PARTNER_ACTIVE,
        )
        db.session.add(self.partner)
        db.session.flush()
        self.mapping = PartnerServiceMapping(
            partner_id=self.partner.id,
            diagnostic_service_id=svc.id,
            partner_service_code="RG-GLU",
            partner_service_name="Glucose",
            price=120000,
            status=MAPPING_ACTIVE,
        )
        db.session.add(self.mapping)
        db.session.commit()
        SlotGenerationService.generate_partner_daily_slots(self.partner.id, days=2)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _order(self):
        slot = SchedulingService.list_available_slots(self.partner.id)[0]
        booking = MarketplaceBookingService.create_booking(
            {
                "partner_service_mapping_id": self.mapping.id,
                "patient_name": "Result Patient",
                "patient_phone": "0909000333",
                "requested_date": slot.slot_date,
            }
        )
        return OrderWorkflowService.create_from_booking(booking.id)

    def test_result_gateway_workflow(self):
        order = self._order()

        manual = self.client.post(
            "/api/v1/results/manual",
            json={
                "medical_order_id": order.id,
                "summary": "Manual glucose result",
                "items": [
                    {
                        "test_code": "GLU",
                        "test_name": "Glucose",
                        "result_value": "5.1",
                        "unit": "mmol/L",
                        "reference_range": "3.9-6.1",
                    }
                ],
                "attachments": [
                    {
                        "file_name": "glucose.pdf",
                        "file_path": "/uploads/results/glucose.pdf",
                        "mime_type": "application/pdf",
                    }
                ],
            },
        )
        self.assertEqual(manual.status_code, 201)
        result_id = manual.get_json()["result"]["id"]
        self.assertEqual(manual.get_json()["result"]["status"], LAB_RESULT_VALIDATED)

        upload = self.client.post(
            "/api/v1/results/upload",
            json={
                "medical_order_id": order.id,
                "analyzer_payload": {"instrument": "DX-100"},
                "items": [
                    {
                        "test_code": "HBA1C",
                        "test_name": "HbA1c",
                        "result_value": "5.8",
                        "unit": "%",
                        "reference_range": "4.0-6.0",
                    }
                ],
            },
        )
        self.assertEqual(upload.status_code, 201)

        listing = self.client.get("/api/v1/results")
        self.assertEqual(listing.status_code, 200)
        self.assertGreaterEqual(listing.get_json()["count"], 2)

        review = self.client.post(
            f"/api/v1/results/{result_id}/review",
            json={"reviewer_email": "pathologist@dxcon.vn", "comments": "Reviewed"},
        )
        self.assertEqual(review.status_code, 200)
        self.assertEqual(review.get_json()["result"]["status"], LAB_RESULT_IN_REVIEW)

        approve = self.client.post(
            f"/api/v1/results/{result_id}/approve",
            json={"approver_email": "chief@dxcon.vn", "comments": "Approved"},
        )
        self.assertEqual(approve.status_code, 200)
        self.assertEqual(approve.get_json()["result"]["status"], LAB_RESULT_APPROVED)

        release = self.client.post(
            f"/api/v1/results/{result_id}/release",
            json={"release_channel": "PATIENT_PORTAL"},
        )
        self.assertEqual(release.status_code, 200)
        self.assertEqual(release.get_json()["result"]["status"], LAB_RESULT_RELEASED)
        self.assertTrue(release.get_json()["result"]["is_locked"])

        detail = self.client.get(f"/api/v1/results/{result_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertIsNotNone(detail.get_json()["release"])

        timeline = self.client.get(f"/api/v1/results/{result_id}/timeline")
        self.assertEqual(timeline.status_code, 200)
        self.assertGreaterEqual(timeline.get_json()["count"], 4)

        locked = LabResult.query.get(result_id)
        self.assertTrue(locked.is_locked)
        release_row = ResultRelease.query.filter_by(lab_result_id=result_id).first()
        self.assertIsNotNone(release_row.payload_json)

        second_release = self.client.post(f"/api/v1/results/{result_id}/release", json={})
        self.assertEqual(second_release.status_code, 409)

    def test_result_gateway_services(self):
        order = self._order()
        result = ResultUploadService.create_manual(
            {
                "medical_order_id": order.id,
                "items": [
                    {
                        "test_name": "Glucose",
                        "result_value": "4.8",
                        "reference_range": "3.9-6.1",
                    }
                ],
            }
        )
        self.assertEqual(result.status, LAB_RESULT_DRAFT)

        from app.services.result_gateway_service import ResultValidationService

        ResultValidationService.validate(result.id)
        ResultReviewService.submit_review(result.id, {"comments": "Needs review"})
        ResultApprovalService.approve(result.id, {"comments": "OK"})
        released, release = ResultReleaseService.release(result.id, {})
        self.assertEqual(released.status, LAB_RESULT_RELEASED)
        self.assertIsNotNone(release.payload_json)

        events = ResultGatewayBase.get_timeline(result.id)
        self.assertGreaterEqual(len(events), 3)

    def test_result_gateway_web_routes(self):
        routes = {str(r) for r in self.app.url_map.iter_rules()}
        for route in ["/results", "/results/upload"]:
            self.assertIn(route, routes)


if __name__ == "__main__":
    unittest.main()
