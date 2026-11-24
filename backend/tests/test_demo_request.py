import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_demo_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

URL = "/api/v1/public/demo-requests"
OK = {"full_name": "Mr Brian", "organization": "Lab A", "email": "a@b.vn", "message": "Hi", "consent_contact": True}


class DemoRequestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.extensions.db import db

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        with cls.app.app_context():
            db.create_all()

    def test_create_ok(self):
        r = self.app.test_client().post(URL, json=OK)
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.get_json()["data"]["reference"].startswith("DM-"))

    def test_requires_consent_and_email(self):
        c = self.app.test_client()
        self.assertEqual(c.post(URL, json={**OK, "consent_contact": False}).status_code, 400)
        self.assertEqual(c.post(URL, json={**OK, "email": "nope"}).status_code, 400)
        self.assertEqual(c.post(URL, json={**OK, "full_name": ""}).status_code, 400)

    def test_honeypot_stores_nothing(self):
        from app.models.demo_request import DemoRequest

        with self.app.app_context():
            before = DemoRequest.query.count()
        r = self.app.test_client().post(URL, json={**OK, "website": "http://spam"})
        self.assertEqual(r.status_code, 201)
        with self.app.app_context():
            self.assertEqual(DemoRequest.query.count(), before)

    def test_rate_limit(self):
        c = self.app.test_client()
        codes = [c.post(URL, json=OK).status_code for _ in range(7)]
        self.assertIn(429, codes)

    def test_list_requires_login(self):
        self.assertIn(self.app.test_client().get("/api/v1/reception/workspace/demo-requests").status_code, (401, 403))


if __name__ == "__main__":
    unittest.main()
