import os
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_extgate_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from app.core.external_role_gate import CLINIC_VIEWER, gate_enabled, is_allowed_path

MESSAGE = "can only use the clinic results lookup"
BLOCKED = [
    ("get", "/api/v1/patients"),
    ("get", "/api/v1/reporting-engine/patient/P1/reports"),
    ("get", "/api/v1/lab-workspace/release/X/html"),
    ("get", "/api/v1/clinic/orders"),
    ("get", "/api/v1/some-new-endpoint"),
    ("get", "/app/system"),
    ("post", "/app/business/orders/X/release"),
]
ALLOWED = ["/api/v1/auth/me", "/api/v1/clinic-results/reports", "/api/v1/system/health", "/login"]


class PathTests(unittest.TestCase):
    def test_allow_list(self):
        for p in ALLOWED + ["/api/v1/auth/memberships", "/static/app.css"]:
            self.assertTrue(is_allowed_path(p), p)

    def test_everything_else_is_not_allowed(self):
        for _, p in BLOCKED + [("get", "/api/v1/auth-evil"), ("get", "/api/v1/clinic-resultsx")]:
            self.assertFalse(is_allowed_path(p), p)

    def test_extra_paths_and_kill_switch(self):
        with patch.dict(os.environ, {"EXTERNAL_GATE_EXTRA_PATHS": "/api/v1/profile, /api/v1/docs/"}):
            self.assertTrue(is_allowed_path("/api/v1/profile"))
            self.assertTrue(is_allowed_path("/api/v1/docs/x"))
            self.assertFalse(is_allowed_path("/api/v1/patients"))
        with patch.dict(os.environ, {"EXTERNAL_ROLE_GATE_ENABLED": "false"}):
            self.assertFalse(gate_enabled())


class GateIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["EXTERNAL_ROLE_GATE_IN_TESTS"] = True
        tag = uuid.uuid4().hex[:6]
        cls.users = {}
        with cls.app.app_context():
            db.create_all()
            for key, role in (("clinic", CLINIC_VIEWER), ("staff", "RECEPTION")):
                email = f"{key}-{tag}@placeholder.dxcon.test"
                user = User(email=email, role=role, password_hash=hash_password("Str0ng-pass-123"), is_active=True)
                db.session.add(user)
                db.session.flush()
                cls.users[key] = (user.id, email, role)
            db.session.commit()

    def _client(self, key):
        client = self.app.test_client()
        if key:
            uid, email, role = self.users[key]
            with client.session_transaction() as s:
                s["user_id"], s["role"], s["email"] = uid, role, email
        return client

    @staticmethod
    def _denied_by_gate(response):
        return response.status_code == 403 and MESSAGE in response.get_data(as_text=True)

    def test_auth_prefix_matches_the_real_routes(self):
        rules = {r.rule for r in self.app.url_map.iter_rules()}
        self.assertIn("/api/v1/auth/me", rules, "adjust ALLOWED_PREFIXES to the real auth URL prefix")

    def test_clinic_user_is_denied_everywhere_else(self):
        client = self._client("clinic")
        for method, path in BLOCKED:
            response = getattr(client, method)(path)
            self.assertTrue(self._denied_by_gate(response), (method, path, response.status_code))

    def test_clinic_user_is_not_denied_on_the_allow_list(self):
        client = self._client("clinic")
        for path in ALLOWED:
            self.assertFalse(self._denied_by_gate(client.get(path)), path)

    def test_staff_and_anonymous_are_not_touched_by_this_gate(self):
        for key in ("staff", None):
            client = self._client(key)
            for method, path in BLOCKED:
                self.assertFalse(self._denied_by_gate(getattr(client, method)(path)), (key, path))

    def test_kill_switch_lets_clinic_user_through_the_gate(self):
        client = self._client("clinic")
        with patch.dict(os.environ, {"EXTERNAL_ROLE_GATE_ENABLED": "false"}):
            self.assertFalse(self._denied_by_gate(client.get("/api/v1/patients")))


if __name__ == "__main__":
    unittest.main()
