import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import CRM_PIPELINE_STAGE_QUALIFICATION, CRM_PIPELINE_STAGES
from app.extensions.db import db
from app.models.crm_lead import CrmLead
from app.models.crm_organization import Customer, Organization
from app.models.crm_pipeline import Opportunity
from app.models.test_catalog import TestCatalog
from app.services.crm_service import CrmService


class CrmTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        CrmService.ensure_default_pipeline()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_lead_crud_and_advance(self):
        lead = CrmService.create_lead(
            {"company_name": "Acme Labs", "contact_person": "Jane", "owner": "sales.alpha"}
        )
        self.assertEqual(lead.pipeline_stage, "LEAD")

        fetched = CrmService.get_lead(lead.id)
        self.assertEqual(fetched["company_name"], "Acme Labs")

        updated = CrmService.update_lead(lead.id, {"status": "QUALIFIED"})
        self.assertEqual(updated.status, "QUALIFIED")

        advanced = CrmService.advance_lead_stage(lead.id)
        self.assertEqual(advanced.pipeline_stage, CRM_PIPELINE_STAGE_QUALIFICATION)

        listing = CrmService.list_leads(q="Acme")
        self.assertGreaterEqual(listing["pagination"]["total"], 1)

        CrmService.delete_lead(lead.id)
        self.assertIsNone(CrmLead.query.get(lead.id))

    def test_customer_and_organization(self):
        org = CrmService.create_organization({"name": "Metro Hospital", "org_type": "HOSPITAL"})
        customer = CrmService.create_customer(
            {"name": "Metro Billing", "organization_id": org.id, "owner": "sales.beta"}
        )
        self.assertEqual(customer.organization_id, org.id)

        orgs = CrmService.list_organizations(q="Metro")
        self.assertGreaterEqual(orgs["pagination"]["total"], 1)

        customers = CrmService.list_customers(organization_id=org.id)
        self.assertGreaterEqual(customers["pagination"]["total"], 1)

    def test_opportunity_workflow(self):
        opp = CrmService.create_opportunity(
            {"title": "Annual screening", "amount": 50000000, "owner": "sales.gamma"}
        )
        self.assertIn(opp.pipeline_stage, CRM_PIPELINE_STAGES)

        advanced = CrmService.advance_opportunity(opp.id)
        self.assertNotEqual(advanced.pipeline_stage, "LEAD")

        payload = CrmService.get_opportunity(opp.id)
        self.assertEqual(payload["title"], "Annual screening")

    def test_activity_timeline(self):
        lead = CrmService.create_lead({"company_name": "Timeline Co"})
        activity = CrmService.create_activity(
            {
                "activity_type": "MEETING",
                "subject": "Discovery call",
                "lead_id": lead.id,
                "owner": "sales.alpha",
            }
        )
        listing = CrmService.list_activities(lead_id=lead.id)
        self.assertGreaterEqual(listing["pagination"]["total"], 1)

        updated = CrmService.update_activity(activity.id, {"is_completed": True})
        self.assertTrue(updated.is_completed)

    def test_pipeline_api(self):
        response = self.client.get("/api/v1/crm/pipelines")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertGreaterEqual(payload["pagination"]["total"], 1)

        response = self.client.post(
            "/api/v1/crm/leads",
            json={"company_name": "API Lead", "contact_person": "Bob"},
        )
        self.assertEqual(response.status_code, 201)

        response = self.client.get("/api/v1/crm/dashboard")
        self.assertEqual(response.status_code, 200)
        dashboard = response.get_json()
        self.assertIn("lead_funnel", dashboard)
        self.assertIn("summary", dashboard)


if __name__ == "__main__":
    unittest.main()
