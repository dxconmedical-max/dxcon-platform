import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.passwords import hash_password
from app.extensions.db import db
from app.integration.parsers.hl7_foundation import parse_hl7_message
from app.integration.webhooks.engine import sign_webhook_payload, verify_webhook_signature
from app.models.user import User
from app.partner_foundation.service import ensure_default_organization


class IntegrationPlatformTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.org = ensure_default_organization()
        self.user = User(
            email="integration@dxcon.test",
            role="ADMIN",
            password_hash=hash_password("DemoPass123!"),
            is_active=True,
            organization_id=self.org.id,
        )
        db.session.add(self.user)
        db.session.commit()
        login = self.client.post(
            "/api/v1/auth/login",
            json={"email": self.user.email, "password": "DemoPass123!"},
        )
        self.token = login.get_json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_connector_crud(self):
        response = self.client.post(
            "/api/v1/integration/connectors",
            headers=self.headers,
            json={
                "connector_code": "LIS-TEST-01",
                "connector_name": "Test LIS",
                "connector_type": "LIS",
                "protocol": "CSV",
                "organization_id": self.org.id,
                "status": "ACTIVE",
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.get_json()["data"]
        self.assertEqual(data["connector_code"], "LIS-TEST-01")
        self.assertTrue(data.get("lis_connector_id"))

    def test_tenant_isolation_denied(self):
        other_org = ensure_default_organization()
        self.client.post(
            "/api/v1/integration/connectors",
            headers=self.headers,
            json={
                "connector_code": "ORG-A",
                "connector_name": "Org A",
                "connector_type": "LIS",
                "protocol": "JSON",
                "organization_id": self.org.id,
            },
        )
        response = self.client.get(
            "/api/v1/integration/connectors?organization_id=00000000-0000-0000-0000-000000000099",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)

    def test_hl7_foundation_parse(self):
        sample = "MSH|^~\\&|S|R|20260101120000||ORU^R01|1|P|2.3\rPID|1||P123||\rOBR|1||O456||\rOBX|1|NM|GLU^Glucose||5.5|mmol/L"
        parsed = parse_hl7_message(sample)
        self.assertTrue(parsed["valid"])
        self.assertEqual(parsed["message_type"], "ORU")

    def test_webhook_hmac(self):
        import time
        secret = "test-secret"
        payload = b'{"event":"order.created"}'
        ts = int(time.time())
        sig = sign_webhook_payload(secret, payload, ts)
        self.assertTrue(verify_webhook_signature(secret, payload, ts, sig))

    def test_duplicate_message_protection(self):
        from app.integration.service import receive_message, upsert_connector

        conn = upsert_connector(
            {
                "connector_code": "DUP-01",
                "connector_name": "Dup",
                "connector_type": "LIS",
                "protocol": "JSON",
                "status": "ACTIVE",
            },
            organization_id=self.org.id,
            actor="test",
        )
        db.session.commit()
        first = receive_message(
            conn["id"],
            organization_id=self.org.id,
            message_type="RESULT_FINAL",
            payload={"order_code": "O1", "test_code": "T1", "result_value": "1"},
            payload_format="JSON",
            external_message_id="EXT-1",
        )
        second = receive_message(
            conn["id"],
            organization_id=self.org.id,
            message_type="RESULT_FINAL",
            payload={"order_code": "O1", "test_code": "T1", "result_value": "1"},
            payload_format="JSON",
            external_message_id="EXT-1",
        )
        self.assertTrue(second.get("duplicate"))

    def test_integration_health(self):
        response = self.client.get("/api/v1/integration/health", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("active_connectors", response.get_json()["data"])


if __name__ == "__main__":
    unittest.main()
