"""RC v1.0.0-rc1 security gate regression tests."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("SECRET_KEY", "rc-test-secret-key-not-for-prod")
os.environ.setdefault("JWT_SECRET_KEY", "rc-test-jwt-secret-key-not-for-prod")

from app import create_app
from app.extensions.db import db
from app.services.refresh_token_service import RefreshTokenService


class RcSecurityGateTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
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

    def test_public_register_rejects_privileged_role(self):
        resp = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "evil-admin@example.com",
                "password": "SecurePass123!",
                "role": "SUPER_ADMIN",
            },
        )
        self.assertEqual(resp.status_code, 403)

    def test_public_register_patient_ok(self):
        resp = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "patient.rc@example.com",
                "password": "SecurePass123!",
                "role": "PATIENT",
            },
        )
        self.assertIn(resp.status_code, (200, 201))

    def test_seed_blocked_in_production(self):
        resp = self.client.post("/api/v1/seeds/demo-operations")
        self.assertEqual(resp.status_code, 403)

    def test_pilot_demo_accounts_blocked_in_production(self):
        resp = self.client.get("/api/v1/pilot-toolkit/demo-accounts")
        self.assertEqual(resp.status_code, 403)

    def test_refresh_unknown_jti_is_revoked(self):
        self.assertTrue(RefreshTokenService.is_revoked("missing-jti-rc1"))

    def test_files_download_requires_signed_token(self):
        resp = self.client.get("/api/v1/files/not-a-real-id/download")
        self.assertEqual(resp.status_code, 401)


class RcApiAuthGateStrictTests(unittest.TestCase):
    """Gate only runs when TESTING is False and APP_ENV is strict."""

    def setUp(self):
        self.app = create_app()
        self.app.config.update(
            {
                "TESTING": False,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "API_AUTH_GATE_ENABLED": True,
                "APP_ENV": "production",
                "DEMO_MODE": False,
                "CORS_ORIGINS": "https://dxcon.com.vn",
                "RATE_LIMIT_ENABLED": False,
                "SECRET_KEY": "rc-test-secret-key-not-for-prod",
                "JWT_SECRET_KEY": "rc-test-jwt-secret-key-not-for-prod",
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

    def test_patients_require_auth_in_production(self):
        resp = self.client.get("/api/v1/patients")
        self.assertEqual(resp.status_code, 401)

    def test_security_users_require_auth_in_production(self):
        resp = self.client.get("/api/v1/security/users")
        self.assertEqual(resp.status_code, 401)

    def test_health_remains_public(self):
        resp = self.client.get("/api/v1/system/health")
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
