import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_apigate_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from app.core.api_extra_gate import gate_enabled, is_protected

PROTECTED = [
    "/api/v1/data-warehouse/facts",
    "/api/v1/backup-recovery/runbook",
    "/api/v1/ai-copilot/audit",
    "/api/v1/ai-operations/cost",
    "/api/v1/ai-v2/generate-all",
    "/api/v1/api-platform/routes",
    "/api/v1/developer-portal/dashboard",
    "/api/v1/system/metrics",
    "/api/v1/system/version",
    "/api/v1/system/build",
]


class PathTests(unittest.TestCase):
    def test_sensitive_paths_are_protected(self):
        for p in PROTECTED:
            self.assertTrue(is_protected(p), p)

    def test_health_live_ready_stay_public(self):
        for p in ("/api/v1/system/health", "/api/v1/system/live", "/api/v1/system/ready"):
            self.assertFalse(is_protected(p), p)

    def test_lookalikes_and_other_groups_are_untouched(self):
        for p in ("/api/v1/ai-copilotx", "/api/v1/ai/reference-ranges", "/api/v1/patients"):
            self.assertFalse(is_protected(p), p)

    def test_extra_public_paths_and_kill_switch(self):
        with patch.dict(os.environ, {"API_EXTRA_GATE_PUBLIC_PATHS": "/api/v1/system/version, /api/v1/data-warehouse/"}):
            self.assertFalse(is_protected("/api/v1/system/version"))
            self.assertFalse(is_protected("/api/v1/data-warehouse/facts"))
            self.assertTrue(is_protected("/api/v1/system/metrics"))
        with patch.dict(os.environ, {"API_EXTRA_GATE_ENABLED": "false"}):
            self.assertFalse(gate_enabled())


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.extensions.db import db

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["API_EXTRA_GATE_IN_TESTS"] = True
        with cls.app.app_context():
            db.create_all()
        cls.client = cls.app.test_client()

    def test_anonymous_requests_to_protected_paths_get_401(self):
        for p in PROTECTED:
            self.assertEqual(self.client.get(p).status_code, 401, p)
        self.assertEqual(self.client.post("/api/v1/ai-v2/generate-all", json={}).status_code, 401)

    def test_health_is_not_blocked(self):
        self.assertNotEqual(self.client.get("/api/v1/system/health").status_code, 401)

    def test_kill_switch_lets_requests_through(self):
        with patch.dict(os.environ, {"API_EXTRA_GATE_ENABLED": "false"}):
            self.assertNotEqual(self.client.get("/api/v1/system/version").status_code, 401)


if __name__ == "__main__":
    unittest.main()
