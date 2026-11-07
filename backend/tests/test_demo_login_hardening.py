import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_demo_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

DEMO_ADMIN = "admin@demo.dxcon.test"
REAL_ADMIN = "real.admin@example.test"


class DemoLoginHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.extensions.db import db

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        with cls.app.app_context():
            db.create_all()

    def _users(self, *specs):
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User

        with self.app.app_context():
            User.query.filter(User.email.in_([DEMO_ADMIN, REAL_ADMIN])).delete(synchronize_session=False)
            for email, role in specs:
                db.session.add(User(email=email, role=role, password_hash=hash_password("Str0ng-pass-123"), is_active=True))
            db.session.commit()

    def _demo(self, path, enabled=True):
        client = self.app.test_client()
        with patch("app.web_gateway.config.demo_mode_enabled", return_value=enabled):
            response = client.get(path)
        with client.session_transaction() as s:
            return response, dict(s)

    def test_disabled_demo_mode_never_logs_in(self):
        self._users((DEMO_ADMIN, "ADMIN"))
        response, sess = self._demo("/login/demo?role=ADMIN", enabled=False)
        self.assertTrue(response.headers["Location"].endswith("/login"))
        self.assertNotIn("role", sess)

    def test_unknown_or_privileged_role_is_rejected(self):
        self._users((DEMO_ADMIN, "ADMIN"))
        for role in ("SUPER_ADMIN", "SYSTEM_ADMIN", "NOBODY"):
            response, sess = self._demo("/login/demo?role=" + role)
            self.assertTrue(response.headers["Location"].endswith("/login"), role)
            self.assertNotIn("role", sess, role)

    def test_no_fake_session_when_demo_user_is_missing(self):
        self._users()
        response, sess = self._demo("/login/demo?role=ADMIN")
        self.assertTrue(response.headers["Location"].endswith("/login"))
        self.assertNotIn("role", sess)
        self.assertNotIn("demo_mode", sess)

    def test_real_admin_is_never_picked_up_by_role(self):
        self._users((REAL_ADMIN, "ADMIN"))
        response, sess = self._demo("/login/demo?role=ADMIN")
        self.assertTrue(response.headers["Location"].endswith("/login"))
        self.assertNotIn("role", sess)

    def test_demo_user_still_works_when_enabled(self):
        self._users((DEMO_ADMIN, "ADMIN"))
        response, sess = self._demo("/login/demo?role=ADMIN")
        self.assertEqual(sess.get("role"), "ADMIN")


if __name__ == "__main__":
    unittest.main()
