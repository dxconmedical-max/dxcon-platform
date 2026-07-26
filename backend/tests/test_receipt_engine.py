"""Receipt Engine tests — issue, preview, print, PDF, reprint, cancel, audit."""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_receipt_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from app import create_app
from app.business_engine import service as biz
from app.models.audit_log import AuditLog
from app.extensions.db import db
from app.models.test_catalog import TestCatalog
from app.models.user import User
from app.reception_workspace.receipt_engine import (
    cancel_receipt,
    generate_receipt_pdf,
    get_receipt,
    preview_receipt,
    reprint_receipt,
)
from app.reception_workspace.service import collect_payment


class ReceiptEngineTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()
        biz.ensure_test_catalog_seed()
        user = User(
            email=f"rcpt-{uuid.uuid4().hex[:6]}@test.local",
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

    def _paid_order(self):
        patient = biz.create_patient(
            full_name="RECEIPT PATIENT",
            phone=f"0977{uuid.uuid4().hex[:6]}",
            patient_code=f"P-R-{uuid.uuid4().hex[:6].upper()}",
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
        paid = collect_payment(
            order.order_code,
            payment_method="cash",
            amount=float(order.total_amount),
            idempotency_key=f"R-{uuid.uuid4().hex[:8]}",
            actor=self.user.email,
        )
        db.session.commit()
        return order, paid

    def test_auto_issue_preview_print_pdf_reprint_cancel(self):
        order, paid = self._paid_order()
        self.assertIn("receipt", paid)
        code = paid["receipt"]["receipt_code"]

        detail = get_receipt(code)
        self.assertEqual(detail["receipt"]["status"], "issued")
        self.assertIn("DxCon Reception Receipt", detail["preview"]["html"])
        self.assertIn("RCT:", detail["preview"]["thermal_text"])

        thermal = preview_receipt(code, format="thermal")
        self.assertEqual(thermal["format"], "thermal")
        self.assertIn("80mm", thermal["html"])

        printed = reprint_receipt(code, format="standard", actor=self.user.email)
        db.session.commit()
        self.assertEqual(printed["receipt"]["status"], "reprinted")
        self.assertGreaterEqual(printed["receipt"]["print_count"], 1)

        pdf = generate_receipt_pdf(code, actor=self.user.email, persist=True)
        db.session.commit()
        self.assertTrue(pdf["pdf_bytes"].startswith(b"%PDF"))
        self.assertTrue(pdf["receipt"]["pdf_available"] or pdf["pdf_path"])

        cancelled = cancel_receipt(code, reason="void desk error", actor=self.user.email)
        db.session.commit()
        self.assertEqual(cancelled["receipt"]["status"], "cancelled")

        with self.assertRaises(Exception):
            reprint_receipt(code, actor=self.user.email)

        audits = AuditLog.query.filter(AuditLog.action.like("reception.receipt_%")).all()
        actions = {a.action for a in audits}
        self.assertTrue(any("receipt_issued" in a for a in actions) or len(audits) >= 1)

        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["role"] = self.user.role
            sess["email"] = self.user.email

        preview = client.get(f"/api/v1/reception/workspace/receipts/{code}/preview?format=thermal")
        self.assertEqual(preview.status_code, 200)
        pdf_http = client.get(f"/api/v1/reception/workspace/receipts/{code}/pdf")
        self.assertEqual(pdf_http.status_code, 400)  # cancelled
        listing = client.get(f"/api/v1/reception/workspace/orders/{order.order_code}/receipts")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.get_json()["data"]["receipts"]), 1)


if __name__ == "__main__":
    unittest.main()
