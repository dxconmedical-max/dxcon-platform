import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.integrations.outbound_signing import OutboundSigningService
from app.webhooks.signatures import verify_inbound_signature, verify_request


class SignatureVerificationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_outbound_and_inbound_match(self):
        payload = {"event_type": "OrderCreated", "order_id": "SIG-1"}
        secret = "test-secret"
        signed = OutboundSigningService.sign_payload(payload, secret=secret)
        self.assertTrue(verify_inbound_signature(secret, signed["payload"], signed["signature"]))

    def test_header_verification(self):
        payload = json.dumps({"status": "ok"})
        secret = self.app.config["INTEGRATION_SIGNING_SECRET"]
        headers = OutboundSigningService.signed_headers(payload, secret=secret)
        self.assertTrue(verify_request(secret, payload, headers))

    def test_invalid_signature_rejected(self):
        payload = json.dumps({"status": "ok"})
        self.assertFalse(verify_inbound_signature("secret", payload, "bad-signature"))


if __name__ == "__main__":
    unittest.main()
