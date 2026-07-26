"""Tests for SUPER_ADMIN Redis diagnostic endpoint."""

from __future__ import annotations

import os
import socket
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from flask_jwt_extended import create_access_token

from app import create_app
from app.core.passwords import hash_password
from app.extensions.db import db
from app.infrastructure.redis_diagnostic import ping_redis_diagnostic, sanitize_error_type
from app.models.user import User


class _FakeRedisError(Exception):
    """Stand-in for redis.exceptions.ConnectionError with DNS message."""


class RedisDiagnosticTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(
            {
                "TESTING": True,
                "REDIS_URL": "redis://red-internal-test:6379/0",
            }
        )
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.super_admin = User(
            email="super-redis@test.local",
            role="SUPER_ADMIN",
            password_hash=hash_password("SecurePass123!"),
            is_active=True,
        )
        self.admin = User(
            email="admin-redis@test.local",
            role="ADMIN",
            password_hash=hash_password("SecurePass123!"),
            is_active=True,
        )
        db.session.add_all([self.super_admin, self.admin])
        db.session.commit()

        self.super_token = create_access_token(
            identity=str(self.super_admin.id),
            additional_claims={"role": "SUPER_ADMIN"},
        )
        self.admin_token = create_access_token(
            identity=str(self.admin.id),
            additional_claims={"role": "ADMIN"},
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _auth(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    def test_unauthenticated_401(self):
        response = self.client.get("/api/v1/system/diagnostics/redis")
        self.assertEqual(response.status_code, 401)
        body = response.get_json() or {}
        blob = str(body).lower()
        self.assertNotIn("redis://", blob)
        self.assertNotIn("password", blob)
        self.assertNotIn("red-internal-test", blob)

    def test_unauthorized_admin_403(self):
        response = self.client.get(
            "/api/v1/system/diagnostics/redis",
            headers=self._auth(self.admin_token),
        )
        self.assertEqual(response.status_code, 403)
        body = response.get_json() or {}
        blob = str(body).lower()
        self.assertNotIn("redis://", blob)
        self.assertNotIn("red-internal-test", blob)

    def test_ping_success(self):
        fake = MagicMock()
        fake.ping.return_value = True
        with patch("app.infrastructure.redis_diagnostic.get_redis_client", return_value=fake):
            response = self.client.get(
                "/api/v1/system/diagnostics/redis",
                headers=self._auth(self.super_token),
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")
        payload = response.get_json()
        self.assertEqual(payload["service"], "redis")
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["ping"])
        self.assertIn(payload["runtime"], {"render", "non_render"})
        self.assertIn("checked_at", payload)
        self.assertNotIn("error_type", payload)
        blob = str(payload).lower()
        self.assertNotIn("redis://", blob)
        self.assertNotIn("red-internal-test", blob)
        self.assertNotIn("password", blob)

    def test_timeout_sanitized(self):
        with patch(
            "app.infrastructure.redis_diagnostic.get_redis_client",
            side_effect=TimeoutError("timed out connecting to redis://secret:pass@red-xxxxx:6379"),
        ):
            response = self.client.get(
                "/api/v1/system/diagnostics/redis",
                headers=self._auth(self.super_token),
            )
        self.assertEqual(response.status_code, 503)
        payload = response.get_json()
        self.assertEqual(payload["status"], "error")
        self.assertFalse(payload["ping"])
        self.assertEqual(payload["error_type"], "TimeoutError")
        blob = str(payload)
        self.assertNotIn("redis://", blob)
        self.assertNotIn("secret", blob)
        self.assertNotIn("pass@", blob)
        self.assertNotIn("red-xxxxx", blob)

    def test_dns_connectivity_sanitized(self):
        exc = _FakeRedisError("Error -2 connecting to red-abcdefghijklm:6379. Name or service not known.")
        exc.__class__.__module__ = "redis.exceptions"
        # Rename dynamically to ConnectionError-like
        class ConnectionError(_FakeRedisError):
            pass

        ConnectionError.__module__ = "redis.exceptions"
        with patch(
            "app.infrastructure.redis_diagnostic.get_redis_client",
            side_effect=ConnectionError("Error -2 connecting to red-abcdefghijklm:6379. Name or service not known."),
        ):
            response = self.client.get(
                "/api/v1/system/diagnostics/redis",
                headers=self._auth(self.super_token),
            )
        payload = response.get_json()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(payload["error_type"], "NameResolutionError")
        self.assertNotIn("red-abcdefghijklm", str(payload))
        self.assertNotIn("6379", str(payload))

    def test_helper_no_secret_in_logs_message(self):
        with self.assertLogs("dxcon.redis_diagnostic", level="INFO") as captured:
            with patch(
                "app.infrastructure.redis_diagnostic.get_redis_client",
                side_effect=socket.gaierror(8, "nodename nor servname provided, or not known"),
            ):
                payload = ping_redis_diagnostic(self.app)
        self.assertFalse(payload["ping"])
        joined = "\n".join(captured.output)
        self.assertNotIn("redis://", joined)
        self.assertNotIn("red-internal-test", joined)
        self.assertIn("error_type=NameResolutionError", joined)

    def test_sanitize_error_type_never_embeds_url(self):
        class Weird(Exception):
            pass

        Weird.__name__ = "redis://user:pass@host"
        self.assertEqual(sanitize_error_type(Weird("x")), "Error")


if __name__ == "__main__":
    unittest.main()
