import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.passwords import verify_password
from app.core.statuses import API_KEY_ACTIVE, API_KEY_REVOKED
from app.extensions.db import db
from app.models.api_platform import ApiKey, ApiUsageLog
from app.services.api_platform_service import ApiClientService, ApiKeyService, ApiUsageService, DeveloperSandboxService


class ApiKeysTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        ApiClientService.ensure_defaults()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_create_client_and_key(self):
        client = self.client.post(
            "/api/v1/api-clients",
            json={"name": "Hospital IT", "organization": "City Hospital"},
        )
        self.assertEqual(client.status_code, 201)
        client_id = client.get_json()["id"]

        created = self.client.post("/api/v1/api-keys", json={"client_id": client_id})
        self.assertEqual(created.status_code, 201)
        payload = created.get_json()
        self.assertIn("api_key", payload)
        self.assertTrue(payload["api_key"].startswith("dxcon_"))
        self.assertEqual(payload["key_prefix"], payload["api_key"][:12])

        row = ApiKey.query.filter_by(id=payload["id"]).first()
        self.assertTrue(verify_password(row.key_hash, payload["api_key"]))
        self.assertNotIn("api_key", row.to_dict())

    def test_revoke_and_usage_logging(self):
        client_id = ApiClientService.list_clients()["clients"][0]["id"]
        key = ApiKeyService.create({"client_id": client_id})
        raw_key = key["api_key"]

        sandbox = DeveloperSandboxService.execute(
            self.app,
            {
                "method": "GET",
                "path": "/api/v1/api-platform/health",
                "headers": {"X-API-Key": raw_key},
            },
        )
        self.assertEqual(sandbox["status_code"], 200)
        self.assertGreaterEqual(ApiUsageLog.query.count(), 1)

        revoked = self.client.post(f"/api/v1/api-keys/{key['id']}/revoke")
        self.assertEqual(revoked.status_code, 200)
        self.assertEqual(revoked.get_json()["status"], API_KEY_REVOKED)

        row = ApiKey.query.filter_by(id=key["id"]).first()
        self.assertEqual(row.status, API_KEY_REVOKED)
        self.assertIsNone(ApiKeyService.authenticate(raw_key))

    def test_usage_listing(self):
        ApiUsageService.log_usage("GET", "/api/v1/api-platform/health", 200, duration_ms=1.2)
        response = self.client.get("/api/v1/api-usage")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.get_json()["count"], 1)


if __name__ == "__main__":
    unittest.main()
