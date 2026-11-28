import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from flask_jwt_extended import create_access_token

from app import create_app
from app.core.passwords import hash_password
from app.extensions.db import db
from app.models.biz_order import BizOrder, BizResult, BizResultItem
from app.models.user import User
from app.services import result_links


def _headers(role):
    user = User(
        email=f"rl-{role.lower()}-{uuid.uuid4().hex[:8]}@test.local",
        role=role,
        password_hash=hash_password("Password123!"),
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()
    token = create_access_token(
        identity=user.id, additional_claims={"role": user.role, "email": user.email}
    )
    return {"Authorization": f"Bearer {token}"}


class ResultLinksTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.order = BizOrder(
            order_code="ORD-RL-1",
            patient_code="P-RL-1",
            patient_name="Nguyen Van A",
            status="released",
            total_amount=1000,
        )
        db.session.add(self.order)
        db.session.flush()
        self.result = BizResult(
            result_code="RES-RL-1",
            order_id=self.order.id,
            status="released",
            patient_visible=True,
            released_at=datetime(2026, 11, 20, 3, 0, 0),
        )
        db.session.add(self.result)
        db.session.flush()
        db.session.add(
            BizResultItem(
                result_id=self.result.id,
                test_name="Glucose",
                result_value="5.2",
                unit="mmol/L",
                reference_range="3.9-6.1",
                flag="NORMAL",
            )
        )
        db.session.commit()
        self.admin = _headers("SUPER_ADMIN")

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _link_token(self):
        res = self.client.post("/api/v1/result-links/ORD-RL-1", headers=self.admin)
        self.assertEqual(res.status_code, 200, res.get_json())
        url = res.get_json()["url"]
        self.assertIn("/r/", url)
        return url.rsplit("/r/", 1)[1]

    def test_staff_creates_link_and_patient_reads_without_login(self):
        token = self._link_token()
        res = self.client.get(f"/api/v1/public/results/{token}")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body["order_code"], "ORD-RL-1")
        self.assertEqual(body["items"][0]["test_name"], "Glucose")
        self.assertEqual(res.headers.get("Cache-Control"), "no-store")
        self.assertNotIn("phone", body)

    def test_garbage_and_tampered_tokens_are_404(self):
        self.assertEqual(self.client.get("/api/v1/public/results/nope").status_code, 404)
        token = self._link_token()
        self.assertEqual(
            self.client.get(f"/api/v1/public/results/{token[:-3]}abc").status_code, 404
        )

    def test_unreleased_result_has_no_link_and_hides_existing_one(self):
        token = self._link_token()
        self.result.patient_visible = False
        db.session.commit()
        self.assertEqual(self.client.get(f"/api/v1/public/results/{token}").status_code, 404)
        res = self.client.post("/api/v1/result-links/ORD-RL-1", headers=self.admin)
        self.assertEqual(res.status_code, 409)

    def test_rerelease_invalidates_old_link(self):
        token = self._link_token()
        self.result.released_at = datetime(2026, 11, 21, 3, 0, 0)
        db.session.commit()
        self.assertEqual(self.client.get(f"/api/v1/public/results/{token}").status_code, 404)

    def test_expired_token_is_rejected(self):
        token = self._link_token()
        original = result_links.MAX_AGE_SECONDS
        result_links.MAX_AGE_SECONDS = -1
        try:
            self.assertEqual(self.client.get(f"/api/v1/public/results/{token}").status_code, 404)
        finally:
            result_links.MAX_AGE_SECONDS = original

    def test_only_internal_staff_create_links(self):
        for role in ("DOCTOR", "COLLECTOR", "LAB"):
            res = self.client.post("/api/v1/result-links/ORD-RL-1", headers=_headers(role))
            self.assertEqual(res.status_code, 403, role)
        res = self.client.post("/api/v1/result-links/ORD-RL-1", headers=_headers("ADMIN"))
        self.assertEqual(res.status_code, 403)

    def test_unknown_order_is_404(self):
        res = self.client.post("/api/v1/result-links/NOPE", headers=self.admin)
        self.assertEqual(res.status_code, 404)

    def test_email_link_needs_config_valid_address_and_never_contains_values(self):
        from unittest import mock

        from app.models.patient import Patient
        from app.notifications import result_email

        url = "/api/v1/result-links/ORD-RL-1/email"
        for role in ("DOCTOR", "COLLECTOR", "LAB"):
            self.assertEqual(self.client.post(url, headers=_headers(role), json={}).status_code, 403, role)
        self.assertEqual(self.client.post("/api/v1/result-links/NOPE/email", headers=self.admin, json={}).status_code, 404)
        # no address anywhere -> 400
        self.assertEqual(self.client.post(url, headers=self.admin, json={}).status_code, 400)
        self.assertEqual(self.client.post(url, headers=self.admin, json={"email": "not-an-email"}).status_code, 400)
        # address given but mail provider not configured -> 503, nothing sent
        with mock.patch.dict(os.environ, {"RESEND_API_KEY": "", "MAIL_FROM": ""}):
            self.assertEqual(self.client.post(url, headers=self.admin, json={"email": "bn@example.com"}).status_code, 503)
        # configured: falls back to the patient's email on file and sends the secure link only
        db.session.add(Patient(patient_code="P-RL-1", full_name="Nguyen Van A", email="Hoa.Nguyen@example.com"))
        db.session.commit()
        sent = {}

        class _Resp:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_urlopen(req, timeout=0):
            import json as _json

            sent.update(_json.loads(req.data.decode("utf-8")))
            return _Resp()

        with mock.patch.dict(os.environ, {"RESEND_API_KEY": "k", "MAIL_FROM": "DxCon <no-reply@dxcon.com.vn>"}):
            with mock.patch.object(result_email.urllib.request, "urlopen", fake_urlopen):
                res = self.client.post(url, headers=self.admin, json={})
        self.assertEqual(res.status_code, 200, res.get_json())
        self.assertEqual(res.get_json()["sent_to"], "ho********@example.com")
        self.assertEqual(sent["to"], ["hoa.nguyen@example.com"])
        self.assertIn("/r/", sent["text"])
        for secret in ("Glucose", "5.2", "mmol"):
            self.assertNotIn(secret, sent["text"] + sent["html"])
        # unreleased result cannot be emailed
        self.result.status = "approved"
        db.session.commit()
        self.assertEqual(self.client.post(url, headers=self.admin, json={"email": "bn@example.com"}).status_code, 409)


if __name__ == "__main__":
    unittest.main()
