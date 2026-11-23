import os
import sys
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from flask_jwt_extended import create_access_token

from app import create_app
from app.core.passwords import hash_password
from app.extensions.db import db
from app.models.biz_order import BizOrder, BizPayment
from app.models.user import User
from app.services import momo

SECRET = "test-secret"
ACCESS = "test-access"


def _headers(role):
    user = User(email=f"mm-{uuid.uuid4().hex[:8]}@test.local", role=role, password_hash=hash_password("Password123!"), is_active=True)
    db.session.add(user)
    db.session.commit()
    token = create_access_token(identity=user.id, additional_claims={"role": role, "email": user.email})
    return {"Authorization": f"Bearer {token}"}


def _ipn(order_code, amount, trans_id="900001", result=0, secret=SECRET):
    data = {
        "partnerCode": "TESTP",
        "orderId": f"{order_code}_abcd1234",
        "requestId": "r1",
        "amount": amount,
        "orderInfo": "DxCon",
        "orderType": "momo_wallet",
        "transId": trans_id,
        "resultCode": result,
        "message": "Successful.",
        "payType": "qr",
        "responseTime": 1700000000000,
        "extraData": "",
        "accessKey": ACCESS,
    }
    data["signature"] = momo.sign(momo._IPN_FIELDS, data, secret)
    data.pop("accessKey")
    return data


class MomoTestCase(unittest.TestCase):
    def setUp(self):
        os.environ.update({"MOMO_PARTNER_CODE": "TESTP", "MOMO_ACCESS_KEY": ACCESS, "MOMO_SECRET_KEY": SECRET, "MOMO_ENV": "test"})
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        db.session.add(
            BizOrder(order_code="ORD-M1", patient_code="P1", patient_name="A", status="payment_pending", subtotal=100000, total_amount=100000)
        )
        db.session.commit()
        self.staff = _headers("SUPER_ADMIN")

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
        for k in ("MOMO_PARTNER_CODE", "MOMO_ACCESS_KEY", "MOMO_SECRET_KEY", "MOMO_ENV"):
            os.environ.pop(k, None)

    def test_create_signs_request_and_returns_qr(self):
        sent = {}

        def fake_post(url, payload):
            sent.update(payload)
            sent["url"] = url
            return {"resultCode": 0, "payUrl": "https://test-payment.momo.vn/pay/x", "qrCodeUrl": "momo://qr/x"}

        with patch.object(momo, "_post", fake_post):
            res = self.client.post("/api/v1/payments/momo/create", json={"order_ref": "ORD-M1"}, headers=self.staff)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertEqual(data["amount"], 100000)
        self.assertTrue(data["qr_png"].startswith("data:image/png"))
        self.assertTrue(sent["url"].endswith("/v2/gateway/api/create"))
        self.assertNotIn("accessKey", sent)
        check = dict(sent, accessKey=ACCESS)
        self.assertEqual(sent["signature"], momo.sign(momo._CREATE_FIELDS, check, SECRET))

    def test_not_configured_returns_503(self):
        os.environ.pop("MOMO_SECRET_KEY")
        res = self.client.post("/api/v1/payments/momo/create", json={"order_ref": "ORD-M1"}, headers=self.staff)
        self.assertEqual(res.status_code, 503)

    def test_ipn_records_payment_once_and_rejects_bad_signature(self):
        bad = self.client.post("/api/v1/public/payments/momo/ipn", json=_ipn("ORD-M1", 100000, secret="wrong"))
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(BizPayment.query.count(), 0)
        ok = self.client.post("/api/v1/public/payments/momo/ipn", json=_ipn("ORD-M1", 100000))
        self.assertEqual(ok.status_code, 204)
        again = self.client.post("/api/v1/public/payments/momo/ipn", json=_ipn("ORD-M1", 100000))
        self.assertEqual(again.status_code, 204)
        self.assertEqual(BizPayment.query.count(), 1)
        self.assertEqual(BizPayment.query.one().payment_method, "momo")
        check = self.client.get("/api/v1/payments/momo/check/ORD-M1", headers=self.staff)
        self.assertTrue(check.get_json()["data"]["paid"])

    def test_failed_payment_records_nothing(self):
        res = self.client.post("/api/v1/public/payments/momo/ipn", json=_ipn("ORD-M1", 100000, result=1006))
        self.assertEqual(res.status_code, 204)
        self.assertEqual(BizPayment.query.count(), 0)

    def test_doctor_cannot_create(self):
        res = self.client.post("/api/v1/payments/momo/create", json={"order_ref": "ORD-M1"}, headers=_headers("DOCTOR"))
        self.assertEqual(res.status_code, 403)


if __name__ == "__main__":
    unittest.main()
