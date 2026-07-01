import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from flask_jwt_extended import create_access_token, create_refresh_token

from app import create_app
from app.core.config_validation import INSECURE_DEFAULTS, config_summary, validate_config
from app.core.permissions import get_role_permissions, role_has_permission
from app.core.rate_limit import rate_limiter
from app.core.security import SECURITY_HEADERS
from app.core.validation import ValidationError, get_json_body, validate_password
from app.extensions.db import db
from app.models.user import User
from app.core.passwords import hash_password


class SecurityTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        rate_limiter.reset()

        self.user = User(
            email="security@test.local",
            role="ADMIN",
            password_hash=hash_password("securepass123"),
            is_active=True,
        )
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_app_creates_with_security(self):
        self.assertIsNotNone(self.app)
        summary = config_summary(self.app)
        self.assertTrue(summary["database_configured"])
        self.assertTrue(summary["security_headers_enabled"])

    def test_config_validation_allows_development_defaults(self):
        self.app.config["APP_ENV"] = "development"
        self.assertTrue(validate_config(self.app))

    def test_config_validation_rejects_production_defaults(self):
        self.app.config["APP_ENV"] = "production"
        self.app.config["SECRET_KEY"] = INSECURE_DEFAULTS["SECRET_KEY"]
        with self.assertRaises(RuntimeError):
            validate_config(self.app)

    def test_security_headers_applied(self):
        response = self.client.get("/api/v1/system/health")
        for header in SECURITY_HEADERS:
            self.assertIn(header, response.headers)

    def test_malformed_json_rejected(self):
        response = self.client.post(
            "/api/v1/auth/login",
            data="not-json",
            content_type="application/json",
        )
        payload = response.get_json()
        self.assertEqual(response.status_code, 422)
        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")

    def test_password_validation(self):
        with self.assertRaises(ValidationError):
            validate_password("short")

    def test_role_permission_helper(self):
        self.assertTrue(role_has_permission("SUPER_ADMIN", "security.write"))
        self.assertTrue(role_has_permission("ADMIN", "security.read"))
        self.assertFalse(role_has_permission("PATIENT", "security.write"))
        self.assertIn("security.read", get_role_permissions("ADMIN"))

    def test_jwt_invalid_token_format(self):
        response = self.client.get(
            "/api/v1/mobile/secure/profile",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        payload = response.get_json()
        self.assertEqual(response.status_code, 401)
        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"]["code"], "INVALID_TOKEN")

    def test_login_and_refresh_flow(self):
        login = self.client.post(
            "/api/v1/auth/login",
            json={"email": "security@test.local", "password": "securepass123"},
        )
        self.assertEqual(login.status_code, 200)
        body = login.get_json()
        self.assertTrue(body["success"])
        self.assertIn("refresh_token", body)

        refresh = self.client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {body['refresh_token']}"},
        )
        self.assertEqual(refresh.status_code, 200)
        self.assertIn("access_token", refresh.get_json())

    def test_logout_revokes_refresh_token(self):
        login = self.client.post(
            "/api/v1/auth/login",
            json={"email": "security@test.local", "password": "securepass123"},
        )
        refresh_token = login.get_json()["refresh_token"]

        logout = self.client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        self.assertEqual(logout.status_code, 200)

        refresh = self.client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        payload = refresh.get_json()
        self.assertEqual(refresh.status_code, 401)
        self.assertEqual(payload["error"]["code"], "TOKEN_REVOKED")

    def test_rate_limit_enforced(self):
        self.app.config["TESTING"] = False
        self.app.config["RATE_LIMIT_ENABLED"] = True
        self.app.config["RATE_LIMIT_MAX"] = 2
        self.app.config["RATE_LIMIT_WINDOW_SECONDS"] = 60
        rate_limiter.reset()

        for _ in range(2):
            response = self.client.get("/api/v1/security/roles")
            self.assertNotEqual(response.status_code, 429)

        limited = self.client.get("/api/v1/security/roles")
        payload = limited.get_json()
        self.assertEqual(limited.status_code, 429)
        self.assertEqual(payload["error"]["code"], "RATE_LIMIT_EXCEEDED")

    def test_secret_key_not_hardcoded_in_app_factory(self):
        self.assertNotEqual(self.app.secret_key, "dxcon-secret-key")


if __name__ == "__main__":
    unittest.main()
