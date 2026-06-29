import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
    PARTNER_APPROVED,
    PARTNER_DRAFT,
    PARTNER_PENDING,
    PARTNER_REJECTED,
    PARTNER_SUBMITTED,
    VERIFICATION_MISSING,
)
from app.extensions.db import db
from app.models.audit_log import AuditLog
from app.models.event_log import EventLog
from app.models.partner import Partner
from app.models.partner_service import PartnerService
from app.models.partner_verification_item import PartnerVerificationItem


class PartnerPlatformTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _create_partner_payload(self, **overrides):
        payload = {
            "partner_type": "LABORATORY",
            "legal_name": "DxCon Test Lab JSC",
            "display_name": "DxCon Test Lab",
            "tax_code": "0101234567",
            "phone": "0901234567",
            "email": "lab@dxcon.test",
            "city": "Hanoi",
            "api_status": "MANUAL_UPLOAD",
            "average_result_time_hours": 24,
            "pickup_sla_minutes": 120,
            "response_sla_minutes": 30,
            "working_hours_summary": "Mon-Sat 07:00-20:00",
        }
        payload.update(overrides)
        return payload

    def _create_partner(self, **overrides):
        response = self.client.post(
            "/api/v1/partners",
            json=self._create_partner_payload(**overrides),
        )
        self.assertEqual(response.status_code, 201)
        return response.get_json()["partner"]

    def test_create_partner_logs_event_and_checklist(self):
        partner = self._create_partner()

        self.assertEqual(partner["status"], PARTNER_DRAFT)
        self.assertTrue(partner["partner_code"].startswith("PTR-LAB-"))
        self.assertEqual(partner["pickup_sla_minutes"], 120)

        db_partner = Partner.query.first()
        self.assertIsNotNone(db_partner)

        event = EventLog.query.filter_by(
            event_type="PARTNER_CREATED",
            object_id=db_partner.id,
        ).first()
        self.assertIsNotNone(event)

        items = PartnerVerificationItem.query.filter_by(partner_id=db_partner.id).all()
        self.assertEqual(len(items), 5)
        self.assertTrue(all(item.status == VERIFICATION_MISSING for item in items))

    def test_list_and_get_partner_detail(self):
        partner = self._create_partner()
        partner_id = partner["id"]

        list_response = self.client.get("/api/v1/partners")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.get_json()["count"], 1)

        get_response = self.client.get(f"/api/v1/partners/{partner_id}?detail=true")
        self.assertEqual(get_response.status_code, 200)
        body = get_response.get_json()
        self.assertEqual(body["partner"]["display_name"], "DxCon Test Lab")
        self.assertEqual(len(body["verification_items"]), 5)

    def test_workflow_submit_and_approve(self):
        partner = self._create_partner()
        partner_id = partner["id"]

        submit_response = self.client.post(f"/api/v1/partners/{partner_id}/submit")
        self.assertEqual(submit_response.status_code, 200)
        self.assertEqual(submit_response.get_json()["partner"]["status"], PARTNER_SUBMITTED)

        approve_response = self.client.post(
            f"/api/v1/partners/{partner_id}/approve",
            json={"verification_note": "Documents verified"},
        )
        self.assertEqual(approve_response.status_code, 200)
        self.assertEqual(approve_response.get_json()["partner"]["status"], PARTNER_APPROVED)

        audit = AuditLog.query.filter_by(
            action="PARTNER_APPROVED",
            object_id=partner_id,
        ).first()
        self.assertIsNotNone(audit)

        event = EventLog.query.filter_by(
            event_type="PARTNER_APPROVED",
            object_id=partner_id,
        ).first()
        self.assertIsNotNone(event)

    def test_legacy_pending_approve_and_reject(self):
        partner = self._create_partner(status=PARTNER_PENDING)
        partner_id = partner["id"]

        approve_response = self.client.post(f"/api/v1/partners/{partner_id}/approve")
        self.assertEqual(approve_response.status_code, 200)
        self.assertEqual(approve_response.get_json()["partner"]["status"], PARTNER_APPROVED)

        partner = self._create_partner(
            display_name="Reject Lab",
            status=PARTNER_PENDING,
        )
        partner_id = partner["id"]

        reject_response = self.client.post(
            f"/api/v1/partners/{partner_id}/reject",
            json={"verification_note": "Missing license"},
        )
        self.assertEqual(reject_response.status_code, 200)
        self.assertEqual(reject_response.get_json()["partner"]["status"], PARTNER_REJECTED)

        audit = AuditLog.query.filter_by(
            action="PARTNER_REJECTED",
            object_id=partner_id,
        ).first()
        self.assertIsNotNone(audit)

    def test_partner_user_and_credentials(self):
        partner = self._create_partner()
        partner_id = partner["id"]

        user_response = self.client.post(
            f"/api/v1/partners/{partner_id}/users",
            json={
                "email": "owner@lab.test",
                "role": "OWNER",
                "status": "INVITED",
            },
        )
        self.assertEqual(user_response.status_code, 201)
        self.assertEqual(user_response.get_json()["user"]["role"], "OWNER")

        credential_response = self.client.post(
            f"/api/v1/partners/{partner_id}/credentials"
        )
        self.assertEqual(credential_response.status_code, 201)
        credential_body = credential_response.get_json()["credential"]
        self.assertIn("client_secret", credential_body)
        self.assertIn("api_key", credential_body)

        list_response = self.client.get(f"/api/v1/partners/{partner_id}/credentials")
        self.assertEqual(list_response.status_code, 200)
        listed = list_response.get_json()["credentials"][0]
        self.assertNotIn("client_secret", listed)
        self.assertNotIn("api_key", listed)
        self.assertNotIn("client_secret_hash", listed)

    def test_partner_services_crud(self):
        partner = self._create_partner()
        partner_id = partner["id"]

        add_response = self.client.post(
            f"/api/v1/partners/{partner_id}/services",
            json={
                "service_code": "CBC",
                "service_name": "Complete Blood Count",
                "catalog_item_code": "TEST-CBC",
                "average_result_time_hours": 6,
            },
        )
        self.assertEqual(add_response.status_code, 201)

        list_response = self.client.get(f"/api/v1/partners/{partner_id}/services")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.get_json()["count"], 1)

        service = PartnerService.query.first()
        self.assertEqual(service.service_code, "CBC")
        self.assertEqual(service.average_result_time_hours, 6)


if __name__ == "__main__":
    unittest.main()
