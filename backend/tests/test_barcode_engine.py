"""Barcode Engine tests — labels, thermal, printer adapters, APIs."""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_barcode_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from app import create_app
from app.business_engine import service as biz
from app.extensions.db import db
from app.models.audit_log import AuditLog
from app.models.test_catalog import TestCatalog
from app.models.user import User
from app.reception_workspace.barcode_engine import (
    build_labels,
    preview_labels,
    print_labels,
)
from app.reception_workspace.errors import ReceptionWorkspaceError
from app.reception_workspace.printers import get_printer, list_printers
from app.reception_workspace.service import collect_payment


class BarcodeEngineTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()
        biz.ensure_test_catalog_seed()
        user = User(
            email=f"bc-{uuid.uuid4().hex[:6]}@test.local",
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
            full_name="BARCODE PATIENT",
            phone=f"0988{uuid.uuid4().hex[:6]}",
            patient_code=f"P-B-{uuid.uuid4().hex[:6].upper()}",
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
        collect_payment(
            order.order_code,
            payment_method="cash",
            amount=float(order.total_amount),
            idempotency_key=f"BC-{uuid.uuid4().hex[:8]}",
            actor=self.user.email,
        )
        db.session.commit()
        return order

    def test_printer_abstraction(self):
        printers = list_printers()
        ids = {p["id"] for p in printers}
        self.assertIn("browser", ids)
        self.assertIn("thermal", ids)
        browser = get_printer("browser")
        thermal = get_printer("thermal")
        job = browser.create_job(
            title="t",
            labels=[{"type": "order", "code": "X"}],
            html="<html/>",
            thermal_text="X\n",
        )
        self.assertEqual(job.printer, "browser")
        self.assertEqual(job.media, "label")
        tjob = thermal.create_job(
            title="t",
            labels=[{"type": "order", "code": "X"}],
            html="<html/>",
            thermal_text="X\n",
        )
        self.assertEqual(tjob.media, "thermal_label")
        self.assertEqual(tjob.meta.get("width_mm"), 80)
        with self.assertRaises(ValueError):
            get_printer("laser-jet-unknown")

    def test_order_sample_collection_labels_and_print(self):
        order = self._paid_order()
        bundle = build_labels(order.order_code)
        types = {lab["type"] for lab in bundle["labels"]}
        self.assertIn("order", types)
        self.assertIn("sample", types)
        self.assertIn("patient", types)
        self.assertIn("collection", types)
        collection = next(lab for lab in bundle["labels"] if lab["type"] == "collection")
        self.assertTrue(collection.get("unavailable"))
        self.assertIsNone(collection.get("code"))

        biz.create_collection_job(
            order.order_code,
            collector_name="Desk",
            pickup_address="Reception",
            actor=self.user.email,
        )
        db.session.commit()

        with_collection = build_labels(order.order_code, types=["order", "sample", "collection"])
        codes = [lab["code"] for lab in with_collection["labels"] if lab.get("code")]
        self.assertTrue(any(str(c).startswith("BC-") for c in codes))
        self.assertTrue(
            any(lab["type"] == "collection" and lab.get("code") for lab in with_collection["labels"])
        )
        self.assertTrue(
            any(lab["type"] == "sample" and lab.get("code") for lab in with_collection["labels"])
        )

        preview = preview_labels(order.order_code, format="thermal", types=["order", "sample"])
        self.assertEqual(preview["format"], "thermal")
        self.assertIn("80mm", preview["html"])
        self.assertIn("Order", preview["thermal_text"])
        self.assertGreater(preview["printable_count"], 0)

        printed = print_labels(
            order.order_code,
            types=["order", "sample", "collection"],
            format="thermal",
            printer="thermal",
            actor=self.user.email,
        )
        db.session.commit()
        self.assertEqual(printed["format"], "thermal")
        self.assertEqual(printed["job"]["printer"], "thermal")
        self.assertTrue(printed["job"]["job_id"].startswith("JOB-"))
        self.assertIn("80mm", printed["job"]["html"])

        audits = AuditLog.query.filter(AuditLog.action.like("%barcode%")).all()
        self.assertGreaterEqual(len(audits), 1)

    def test_print_rejects_when_no_printable(self):
        order = self._paid_order()
        with self.assertRaises(ReceptionWorkspaceError):
            print_labels(order.order_code, types=["collection"], printer="browser")

    def test_api_labels_preview_print_printers(self):
        order = self._paid_order()
        biz.create_collection_job(
            order.order_code,
            collector_name="Desk",
            pickup_address="Reception",
            actor=self.user.email,
        )
        db.session.commit()

        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["role"] = self.user.role
            sess["email"] = self.user.email

        labels = client.get(
            f"/api/v1/reception/workspace/orders/{order.order_code}/barcode/labels"
        )
        self.assertEqual(labels.status_code, 200)
        self.assertTrue(labels.get_json()["data"]["labels"])

        preview = client.get(
            f"/api/v1/reception/workspace/orders/{order.order_code}/barcode/preview"
            "?format=thermal&types=order,sample"
        )
        self.assertEqual(preview.status_code, 200)
        self.assertIn("html", preview.get_json()["data"])

        printers = client.get("/api/v1/reception/workspace/barcode/printers")
        self.assertEqual(printers.status_code, 200)
        self.assertGreaterEqual(len(printers.get_json()["data"]["printers"]), 2)

        printed = client.post(
            f"/api/v1/reception/workspace/orders/{order.order_code}/barcode/print",
            json={"types": ["order", "sample"], "format": "standard", "printer": "browser"},
        )
        self.assertEqual(printed.status_code, 200)
        self.assertIn("job", printed.get_json()["data"])

        bundled = client.get(
            f"/api/v1/reception/workspace/orders/{order.order_code}/barcode?labels=1"
        )
        self.assertEqual(bundled.status_code, 200)
        body = bundled.get_json()["data"]
        self.assertIn("labels", body)
        self.assertIn("order_barcode", body["barcodes"])


if __name__ == "__main__":
    unittest.main()
