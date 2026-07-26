"""QR Engine tests — payment, VNPay, static/dynamic, sample, tracking, verify."""

from __future__ import annotations

import os
import tempfile
import time
import unittest
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_qr_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"
os.environ["DXCON_QR_SECRET"] = "test-qr-secret"

from app import create_app
from app.business_engine import service as biz
from app.extensions.db import db
from app.models.test_catalog import TestCatalog
from app.models.user import User
from app.reception_workspace.qr_engine import (
    PREFIX_DYN,
    PREFIX_PAY,
    PREFIX_VNPAY,
    build_dynamic_qr,
    build_payment_qr,
    build_qr_bundle,
    build_vnpay_qr,
    verify_qr_payload,
)
from app.reception_workspace.service import collect_payment


class QrEngineTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()
        biz.ensure_test_catalog_seed()
        user = User(
            email=f"qr-{uuid.uuid4().hex[:6]}@test.local",
            role="RECEPTION",
            password_hash="x",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        self.user = user
        self.test = TestCatalog.query.first()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _order(self, *, pay: bool = False):
        patient = biz.create_patient(
            full_name="QR PATIENT",
            phone=f"0911{uuid.uuid4().hex[:6]}",
            patient_code=f"P-Q-{uuid.uuid4().hex[:6].upper()}",
            actor=self.user.email,
        )
        order = biz.create_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.test.id],
            actor=self.user.email,
        )
        biz.submit_order_for_payment(order.order_code, actor=self.user.email)
        biz.create_invoice_from_order(order.order_code, actor=self.user.email)
        db.session.commit()
        if pay:
            collect_payment(
                order.order_code,
                payment_method="cash",
                amount=float(order.total_amount),
                idempotency_key=f"QR-{uuid.uuid4().hex[:8]}",
                actor=self.user.email,
            )
            db.session.commit()
        return order

    def test_payment_and_vnpay_qr(self):
        order = self._order(pay=False)
        pay = build_payment_qr(order)
        self.assertTrue(pay["payload"].startswith(PREFIX_PAY))
        self.assertTrue(pay["image_data_url"].startswith("data:image/png;base64,"))
        verified = verify_qr_payload(pay["payload"], order_ref=order.order_code)
        self.assertTrue(verified["valid"])
        self.assertEqual(verified["kind"], "payment")

        vnp = build_vnpay_qr(order)
        self.assertTrue(vnp["payload"].startswith(PREFIX_VNPAY))
        self.assertEqual(vnp["meta"]["provider"], "VNPAY")
        self.assertIn("sandbox.vnpayment.vn", vnp["meta"]["payment_url"])
        v_ok = verify_qr_payload(vnp["payload"], order_ref=order.order_code)
        self.assertTrue(v_ok["valid"])
        self.assertEqual(v_ok["kind"], "vnpay")

    def test_static_dynamic_sample_tracking_and_verify(self):
        order = self._order(pay=True)
        bundle = build_qr_bundle(order.order_code)
        kinds = {q["kind"] for q in bundle["qrs"] if not q.get("unavailable")}
        self.assertIn("payment", kinds)
        self.assertIn("vnpay", kinds)
        self.assertIn("static", kinds)
        self.assertIn("dynamic", kinds)
        self.assertIn("sample", kinds)
        self.assertIn("tracking", kinds)

        statics = [q for q in bundle["qrs"] if q["kind"] == "static"]
        self.assertEqual(len(statics), 2)
        for card in statics:
            self.assertTrue(verify_qr_payload(card["payload"])["valid"])

        dyn = next(q for q in bundle["qrs"] if q["kind"] == "dynamic")
        self.assertTrue(dyn["payload"].startswith(PREFIX_DYN))
        self.assertTrue(verify_qr_payload(dyn["payload"], order_ref=order.order_code)["valid"])

        samples = [q for q in bundle["qrs"] if q["kind"] == "sample"]
        self.assertGreaterEqual(len(samples), 1)
        self.assertTrue(verify_qr_payload(samples[0]["payload"])["valid"])

        track = next(q for q in bundle["qrs"] if q["kind"] == "tracking")
        self.assertTrue(verify_qr_payload(track["payload"])["valid"])

        # Tampered dynamic fails
        bad = dyn["payload"][:-4] + "dead"
        self.assertFalse(verify_qr_payload(bad)["valid"])

        # Expired dynamic
        expired = build_dynamic_qr(order, ttl_sec=60)
        # rewrite expiry in the past by reconstructing
        parts = expired["payload"][len(PREFIX_DYN) :].split(":")
        purpose, order_code, nonce, _exp, _sig = parts
        past = str(int(time.time()) - 10)
        from app.reception_workspace.qr_engine import _sign

        sig = _sign([purpose, order_code, nonce, past])
        stale = f"{PREFIX_DYN}{purpose}:{order_code}:{nonce}:{past}:{sig}"
        stale_result = verify_qr_payload(stale)
        self.assertFalse(stale_result["valid"])
        self.assertIn("expired", (stale_result["reason"] or "").lower())

    def test_sample_unavailable_when_unpaid(self):
        order = self._order(pay=False)
        bundle = build_qr_bundle(order.order_code, kinds=["sample"])
        self.assertTrue(bundle["qrs"][0].get("unavailable"))

    def test_api_bundle_preview_verify_kinds(self):
        order = self._order(pay=True)
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["role"] = self.user.role
            sess["email"] = self.user.email

        kinds = client.get("/api/v1/reception/workspace/qr/kinds")
        self.assertEqual(kinds.status_code, 200)
        self.assertGreaterEqual(len(kinds.get_json()["data"]["kinds"]), 6)

        bundle = client.get(
            f"/api/v1/reception/workspace/orders/{order.order_code}/qr"
            "?kinds=payment,static,tracking&preview=1"
        )
        self.assertEqual(bundle.status_code, 200)
        data = bundle.get_json()["data"]
        self.assertIn("html", data)
        self.assertTrue(data["qrs"])

        payload = data["qrs"][0]["payload"]
        verify = client.post(
            "/api/v1/reception/workspace/qr/verify",
            json={"payload": payload, "order_ref": order.order_code},
        )
        self.assertEqual(verify.status_code, 200)
        self.assertTrue(verify.get_json()["data"]["valid"])

        preview = client.get(
            f"/api/v1/reception/workspace/orders/{order.order_code}/qr/preview?kinds=vnpay"
        )
        self.assertEqual(preview.status_code, 200)
        self.assertIn("html", preview.get_json()["data"])


if __name__ == "__main__":
    unittest.main()
