import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.passwords import hash_password
from app.core.rate_limit import rate_limiter
from app.extensions.db import db
from app.models.user import User


class LoginThrottleTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["LOGIN_THROTTLE_IN_TESTS"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        rate_limiter.reset()
        db.session.add(User(email="throttle@test.local", role="ADMIN",
                            password_hash=hash_password("securepass123"), is_active=True))
        db.session.commit()

    def tearDown(self):
        rate_limiter.reset()
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _login(self, password):
        return self.client.post("/api/v1/auth/login",
                                json={"email": "throttle@test.local", "password": password})

    def test_locks_after_repeated_failures_then_blocks_correct_password(self):
        for _ in range(10):
            self.assertEqual(self._login("wrong-password-1").status_code, 401)
        self.assertEqual(self._login("wrong-password-1").status_code, 429)
        self.assertEqual(self._login("securepass123").status_code, 429)

    def test_success_clears_failure_count(self):
        for _ in range(5):
            self._login("wrong-password-1")
        self.assertEqual(self._login("securepass123").status_code, 200)
        for _ in range(9):
            self.assertEqual(self._login("wrong-password-1").status_code, 401)

    def test_unknown_email_is_throttled_too(self):
        for _ in range(10):
            r = self.client.post("/api/v1/auth/login",
                                 json={"email": "nobody@test.local", "password": "wrong-password-1"})
            self.assertEqual(r.status_code, 401)
        r = self.client.post("/api/v1/auth/login",
                             json={"email": "nobody@test.local", "password": "wrong-password-1"})
        self.assertEqual(r.status_code, 429)


class RequestFormEscapeTestCase(unittest.TestCase):
    def test_request_form_escapes_user_text(self):
        from types import SimpleNamespace
        from app.business_engine.service import render_request_form_html

        order = SimpleNamespace(
            order_code="O-1", patient_name="<script>alert(1)</script>", patient_code="P<1>",
            barcode_value="<b>x</b>", total_amount=10,
            items=[SimpleNamespace(test_name="<img src=x onerror=1>", test_code="T&1", line_total=10)],
        )
        html = render_request_form_html(order)
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img", html)
        self.assertIn("&lt;script&gt;", html)


if __name__ == "__main__":
    unittest.main()
