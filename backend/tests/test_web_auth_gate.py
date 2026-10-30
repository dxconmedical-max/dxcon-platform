import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_webgate_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from app.core.web_auth_gate import gate_enabled, is_public_path


class PublicPathTests(unittest.TestCase):
    def test_health_login_static_and_api_are_public(self):
        for p in ("/health", "/live", "/login", "/static/app.css", "/api/v1/anything"):
            self.assertTrue(is_public_path(p), p)

    def test_pages_with_data_are_not_public(self):
        for p in ("/patients", "/marketplace/bookings", "/audit", "/orders", "/collector-mobile", "/demo-accounts"):
            self.assertFalse(is_public_path(p), p)

    def test_lookalike_prefixes_are_not_public(self):
        for p in ("/healthcare-ecosystem", "/live-data", "/login-help", "/staticfiles"):
            self.assertFalse(is_public_path(p), p)

    def test_extra_paths_from_env(self):
        with patch.dict(os.environ, {"WEB_AUTH_GATE_PUBLIC_PATHS": "/demo-landing, /docs/"}):
            self.assertTrue(is_public_path("/demo-landing"))
            self.assertTrue(is_public_path("/docs/intro"))
            self.assertFalse(is_public_path("/patients"))

    def test_kill_switch(self):
        with patch.dict(os.environ, {"WEB_AUTH_GATE_ENABLED": "false"}):
            self.assertFalse(gate_enabled())
        with patch.dict(os.environ, {"WEB_AUTH_GATE_ENABLED": "true"}):
            self.assertTrue(gate_enabled())


class GateIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.extensions.db import db

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["WEB_AUTH_GATE_IN_TESTS"] = True
        with cls.app.app_context():
            db.create_all()
        cls.client = cls.app.test_client()

    def test_anonymous_pages_redirect_to_login(self):
        for p in ("/marketplace/bookings", "/patients", "/orders", "/audit"):
            r = self.client.get(p)
            self.assertEqual(r.status_code, 302, p)
            self.assertTrue(r.headers["Location"].endswith("/login"), p)

    def test_anonymous_post_is_rejected(self):
        self.assertEqual(self.client.post("/marketplace/book", data={}).status_code, 401)


if __name__ == "__main__":
    unittest.main()
