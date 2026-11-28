"""Anonymous API access is denied by default in production; only an explicit public list stays open."""

from __future__ import annotations

import os
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("SECRET_KEY", "rc-test-secret-key-not-for-prod")
os.environ.setdefault("JWT_SECRET_KEY", "rc-test-jwt-secret-key-not-for-prod")

from flask_jwt_extended import create_access_token

from app import create_app
from app.core.passwords import hash_password
from app.extensions.db import db
from app.models.user import User


class ApiDefaultDenyTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(
            {
                "TESTING": True,
                "API_AUTH_GATE_IN_TESTS": True,
                "API_AUTH_GATE_ENABLED": True,
                "APP_ENV": "production",
                "DEMO_MODE": False,
                "CORS_ORIGINS": "https://dxcon.com.vn",
                "RATE_LIMIT_ENABLED": False,
            }
        )
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _auth(self, role):
        user = User(
            email=f"dd-{role.lower()}-{uuid.uuid4().hex[:6]}@test.local",
            role=role,
            password_hash=hash_password("Password123!"),
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        token = create_access_token(identity=user.id, additional_claims={"role": role, "email": user.email})
        return {"Authorization": f"Bearer {token}"}

    def test_anonymous_is_denied_on_modules_that_used_to_be_open(self):
        for path in (
            "/api/v1/result-files",
            "/api/v1/enterprise-analytics/dashboard",
            "/api/v1/executive-metrics/dashboard",
            "/api/v1/device-gateway/dashboard",
            "/api/v1/box-qr/test",
            "/api/v1/openapi.json",
            "/api/v1/a-module-nobody-listed/anything",  # default-deny: new modules are closed from day one
        ):
            self.assertEqual(self.client.get(path).status_code, 401, path)

    def test_explicit_public_endpoints_stay_open(self):
        self.assertEqual(self.client.get("/api/v1/system/health").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/public/results/garbage").status_code, 404)
        for path in (
            "/api/v1/auth/forgot-password",
            "/api/v1/public/bookings",
            "/api/v1/public/demo-requests",
            "/api/v1/pilot-readiness/partner-registration",
            "/api/v1/iot/readings/temperature",
        ):
            self.assertNotEqual(self.client.post(path, json={}).status_code, 401, path)

    def test_unsigned_webhooks_and_ingest_are_closed(self):
        for path in (
            "/api/v1/payments/webhook",
            "/api/v1/marketplace/v2/payments/webhook",
            "/api/v1/integrations/lis/orders",
            "/api/v1/integrations/lis/results",
            "/api/v1/integrations/his/patients",
        ):
            self.assertEqual(self.client.post(path, json={}).status_code, 401, path)

    def test_logged_in_non_admin_cannot_use_back_office_modules(self):
        reception = self._auth("RECEPTION")
        for path in ("/api/v1/result-files", "/api/v1/enterprise-analytics/dashboard", "/api/v1/executive-metrics/dashboard"):
            self.assertEqual(self.client.get(path, headers=reception).status_code, 403, path)
        self.assertEqual(self.client.get("/api/v1/result-files", headers=self._auth("ADMIN")).status_code, 200)

    def test_authenticated_callers_still_cannot_forge_payments_or_ingest(self):
        reception, admin = self._auth("RECEPTION"), self._auth("ADMIN")
        self.assertEqual(self.client.post("/api/v1/payments/webhook", headers=admin, json={"provider": "STRIPE"}).status_code, 403)
        self.assertEqual(self.client.post("/api/v1/integrations/lis/orders", headers=reception, json={}).status_code, 403)
        self.assertEqual(self.client.post("/api/v1/integrations/lis/orders", headers=admin, json={}).status_code, 400)  # passes the guard, needs connection_id

    def test_marketplace_webhook_has_no_default_secret_in_production(self):
        os.environ.pop("MARKETPLACE_PAYMENT_WEBHOOK_SECRET", None)
        resp = self.client.post("/api/v1/marketplace/v2/payments/webhook", headers=self._auth("ADMIN"), json={})
        self.assertEqual(resp.status_code, 503)


if __name__ == "__main__":
    unittest.main()
