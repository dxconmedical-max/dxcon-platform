"""Payment Engine tests — partial, methods, history, state machine."""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_payeng_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from app import create_app
from app.business_engine import service as biz
from app.business_engine.statuses import ORDER_PAID, ORDER_PAYMENT_PENDING
from app.extensions.db import db
from app.models.test_catalog import TestCatalog
from app.models.user import User
from app.reception_workspace import payment_engine as payeng
from app.reception_workspace.errors import ReceptionWorkspaceError
from app.reception_workspace.service import (
    collect_payment,
    get_order_with_payment,
    get_payment_history,
)


class PaymentEngineTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()
        biz.ensure_test_catalog_seed()
        user = User(
            email=f"pay-{uuid.uuid4().hex[:6]}@test.local",
            role="RECEPTION",
            password_hash="x",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        self.user = user
        self.test = TestCatalog.query.first()
        self.assertIsNotNone(self.test)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _order(self, *, discount: float = 0):
        patient = biz.create_patient(
            full_name="PAY ENG PATIENT",
            phone=f"0988{uuid.uuid4().hex[:6]}",
            patient_code=f"P-PE-{uuid.uuid4().hex[:6].upper()}",
            actor=self.user.email,
        )
        order = biz.create_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.test.id],
            discount=discount,
            actor=self.user.email,
        )
        biz.submit_order_for_payment(order.order_code, actor=self.user.email)
        biz.create_invoice_from_order(order.order_code, actor=self.user.email)
        db.session.commit()
        return order

    def test_method_aliases_cash_and_bank_transfer(self):
        self.assertEqual(payeng.validate_payment_method("cash"), "cash")
        self.assertEqual(payeng.validate_payment_method("bank_transfer"), "transfer")
        self.assertEqual(payeng.validate_payment_method("transfer"), "transfer")
        with self.assertRaises(ReceptionWorkspaceError):
            payeng.validate_payment_method("crypto")

    def test_partial_then_full_with_history_and_state(self):
        order = self._order()
        total = float(order.total_amount)
        half = round(total / 2, 2)
        if half <= 0 or half >= total:
            half = round(max(1.0, total - 1), 2)

        first = collect_payment(
            order.order_code,
            payment_method="cash",
            amount=half,
            idempotency_key=f"P1-{uuid.uuid4().hex[:8]}",
            actor=self.user.email,
        )
        db.session.commit()
        self.assertEqual(first["payment_summary"]["status"], "partial")
        self.assertEqual(first["order_status"], ORDER_PAYMENT_PENDING)
        self.assertEqual(len(first["payments"]), 1)

        hist = get_payment_history(order.order_code)
        self.assertEqual(len(hist["payments"]), 1)
        self.assertTrue(hist["payment_summary"]["partial_payments_supported"])

        rest = float(first["payment_summary"]["outstanding_amount"])
        second = collect_payment(
            order.order_code,
            payment_method="bank_transfer",
            amount=rest,
            idempotency_key=f"P2-{uuid.uuid4().hex[:8]}",
            actor=self.user.email,
        )
        db.session.commit()
        self.assertEqual(second["payment"]["payment_method"], "transfer")
        self.assertEqual(second["payment_summary"]["status"], "paid")
        self.assertEqual(second["order_status"], ORDER_PAID)
        self.assertEqual(len(second["payments"]), 2)

        detail = get_order_with_payment(order.order_code)
        self.assertEqual(len(detail["payments"]), 2)
        methods = {p["payment_method"] for p in detail["payments"]}
        self.assertEqual(methods, {"cash", "transfer"})

    def test_http_payment_history_route(self):
        order = self._order()
        collect_payment(
            order.order_code,
            payment_method="qr",
            amount=float(order.total_amount),
            idempotency_key=f"H-{uuid.uuid4().hex[:8]}",
            actor=self.user.email,
        )
        db.session.commit()

        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["role"] = self.user.role
            sess["email"] = self.user.email

        res = client.get(f"/api/v1/reception/workspace/orders/{order.order_code}/payments")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body["success"])
        self.assertEqual(len(body["data"]["payments"]), 1)
        self.assertEqual(body["data"]["payment_summary"]["status"], "paid")

    def test_validation_overpay_and_zero(self):
        with self.assertRaises(ReceptionWorkspaceError):
            payeng.validate_payment_amount(0, 100)
        with self.assertRaises(ReceptionWorkspaceError):
            payeng.validate_payment_amount(150, 100)
        self.assertEqual(payeng.validate_payment_amount(40, 100), 40.0)
        self.assertEqual(payeng.validate_payment_amount(None, 100), 100.0)

    def test_state_machine_transitions(self):
        payeng.assert_payment_transition("unpaid", "partial")
        payeng.assert_payment_transition("partial", "paid")
        with self.assertRaises(ReceptionWorkspaceError):
            payeng.assert_payment_transition("paid", "partial")


if __name__ == "__main__":
    unittest.main()
