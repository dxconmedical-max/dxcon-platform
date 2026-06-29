import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.company import Company
from app.models.integration_audit_log import IntegrationAuditLog
from app.models.integration_message import IntegrationMessage
from scripts.seed_integrations_demo import seed_integrations_demo


class IntegrationsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        db.session.add(Company(company_code="DX", company_name="DxCon", tax_code="01"))
        db.session.commit()
        self.demo = seed_integrations_demo()
        self.connection_id = self.demo["connection_id"]

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_integrations_apis(self):
        connections = self.client.get("/api/v1/integrations/connections")
        self.assertEqual(connections.status_code, 200)
        self.assertGreaterEqual(connections.get_json()["count"], 1)

        create = self.client.post(
            "/api/v1/integrations/connections",
            json={
                "partner_code": "LIS-TEST-002",
                "partner_name": "Test LIS",
                "integration_type": "LIS",
                "connection_code": "LIS-CONN-TEST",
            },
        )
        self.assertEqual(create.status_code, 201)
        conn_id = create.get_json()["connection"]["id"]

        order = self.client.post(
            "/api/v1/integrations/lis/orders",
            json={
                "connection_id": conn_id,
                "external_order_id": "LIS-ORD-TEST",
                "patient_code": "PAT-TEST",
                "test_codes": ["GLU"],
            },
        )
        self.assertEqual(order.status_code, 201)

        result = self.client.post(
            "/api/v1/integrations/lis/results",
            json={
                "connection_id": conn_id,
                "external_order_id": "LIS-ORD-TEST",
                "result_code": "GLU",
                "result_value": "6.1",
            },
        )
        self.assertEqual(result.status_code, 201)

        patient = self.client.post(
            "/api/v1/integrations/his/patients",
            json={
                "connection_id": self.demo["his_connection_id"],
                "external_patient_id": "HIS-PAT-TEST",
                "full_name": "Test HIS Patient",
                "phone": "0908999000",
            },
        )
        self.assertEqual(patient.status_code, 201)

        messages = self.client.get("/api/v1/integrations/messages")
        self.assertEqual(messages.status_code, 200)
        self.assertGreaterEqual(messages.get_json()["count"], 1)

        audit = self.client.get("/api/v1/integrations/audit")
        self.assertEqual(audit.status_code, 200)
        self.assertGreaterEqual(audit.get_json()["count"], 1)
        self.assertGreaterEqual(IntegrationAuditLog.query.count(), 1)
        self.assertGreaterEqual(IntegrationMessage.query.count(), 1)

    def test_integrations_web_routes(self):
        routes = {str(r) for r in self.app.url_map.iter_rules()}
        for route in ["/integrations", "/integrations/connections", "/integrations/messages"]:
            self.assertIn(route, routes)


if __name__ == "__main__":
    unittest.main()
