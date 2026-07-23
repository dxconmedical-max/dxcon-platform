"""Tests for Sprint 006 reception operational workspace."""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid

# File-backed SQLite: schema introspection opens a second connection; :memory:
# would otherwise wipe the DB mid-request (see table_exists_name).
_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_reception_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from app import create_app
from app.business_engine import service as biz
from app.extensions.db import db
from app.models.user import User
from app.reception_workspace.service import duplicate_warnings, fast_search_patients, workspace_dashboard


class ReceptionWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()
        biz.ensure_test_catalog_seed()
        user = User(
            email=f"reception-{uuid.uuid4().hex[:6]}@test.local",
            role="RECEPTION",
            password_hash="x",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        self.user = user

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_workspace_dashboard(self):
        dash = workspace_dashboard()
        self.assertIn("kpis", dash)
        self.assertGreaterEqual(len(dash.get("widgets", [])), 8)

    def test_fast_search_empty_query(self):
        result = fast_search_patients("")
        self.assertIn("data", result)
        self.assertIn("pagination", result)

    def test_milestone1_order_get_route_and_optional_patient_code(self):
        """GET /orders/:ref is mounted; register_patient accepts patient_code."""
        from app.reception_workspace.service import register_patient

        code = f"P-M1-{uuid.uuid4().hex[:6].upper()}"
        phone = f"0900{uuid.uuid4().hex[:6]}"
        result = register_patient(
            {
                "full_name": "E2E RECEPTION TEST UNIT",
                "phone": phone,
                "patient_code": code,
                "force": True,
            },
            actor=self.user.email,
            force=True,
        )
        db.session.commit()
        self.assertTrue(result.get("ok"))
        self.assertEqual(result["patient"]["patient_code"], code)

        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["role"] = self.user.role
            sess["email"] = self.user.email

        missing = client.get("/api/v1/reception/workspace/orders/DOES-NOT-EXIST-M1")
        self.assertEqual(missing.status_code, 404)
        self.assertFalse(missing.get_json().get("success"))


    def test_milestone2_payment_collect_idempotent_and_overpay(self):
        """Full collect, idempotent replay, overpay, and partial reject."""
        from app.reception_workspace.service import (
            collect_payment,
            get_order_with_payment,
            payment_summary_for_order,
        )
        from app.models.biz_order import BizOrder
        from app.models.test_catalog import TestCatalog

        # Use biz patient/order path (avoid register_patient → create_queue_entry
        # which calls table_exists_name via db.engine and wipes sqlite :memory:).
        phone = f"0911{uuid.uuid4().hex[:6]}"
        patient = biz.create_patient(
            full_name="M2 PAYMENT PATIENT",
            phone=phone,
            patient_code=f"P-M2-{uuid.uuid4().hex[:6].upper()}",
            actor=self.user.email,
        )
        db.session.commit()

        test = TestCatalog.query.first()
        self.assertIsNotNone(test)
        order = biz.create_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[test.id],
            actor=self.user.email,
        )
        biz.submit_order_for_payment(order.order_code, actor=self.user.email)
        biz.create_invoice_from_order(order.order_code, actor=self.user.email)
        db.session.commit()

        order_code = order.order_code
        total = float(order.total_amount)
        self.assertGreater(total, 0)

        detail = get_order_with_payment(order_code)
        self.assertEqual(detail["payment_summary"]["status"], "unpaid")
        self.assertEqual(detail["payment_summary"]["outstanding_amount"], total)
        self.assertFalse(detail["payment_summary"]["partial_payments_supported"])
        self.assertIsNone(detail["payment"])
        self.assertIn("pricing", detail)

        with self.assertRaisesRegex(Exception, "Partial payments"):
            collect_payment(
                order_code,
                payment_method="cash",
                amount=total / 2,
                actor=self.user.email,
            )

        with self.assertRaisesRegex(Exception, "Overpayment|overpay"):
            collect_payment(
                order_code,
                payment_method="cash",
                amount=total + 1000,
                actor=self.user.email,
            )

        with self.assertRaisesRegex(Exception, "Invalid payment method"):
            collect_payment(
                order_code,
                payment_method="bitcoin",
                amount=total,
                actor=self.user.email,
            )

        with self.assertRaisesRegex(Exception, "greater than zero"):
            collect_payment(
                order_code,
                payment_method="cash",
                amount=0,
                actor=self.user.email,
            )

        key = f"IDEM-{uuid.uuid4().hex[:10].upper()}"
        first = collect_payment(
            order_code,
            payment_method="cash",
            amount=total,
            idempotency_key=key,
            actor=self.user.email,
        )
        db.session.commit()
        self.assertFalse(first.get("idempotent_replay"))
        self.assertEqual(first["payment"]["receipt_number"], key)
        self.assertEqual(first["payment_summary"]["status"], "paid")
        self.assertEqual(first["payment_summary"]["outstanding_amount"], 0)

        replay = collect_payment(
            order_code,
            payment_method="cash",
            amount=total,
            idempotency_key=key,
            actor=self.user.email,
        )
        self.assertTrue(replay.get("idempotent_replay"))
        self.assertEqual(replay["payment"]["receipt_number"], key)

        already = collect_payment(
            order_code,
            payment_method="transfer",
            amount=total,
            idempotency_key=f"OTHER-{uuid.uuid4().hex[:8]}",
            actor=self.user.email,
        )
        self.assertTrue(already.get("idempotent_replay"))
        self.assertEqual(already["payment"]["receipt_number"], key)

        paid_detail = get_order_with_payment(order_code)
        self.assertEqual(paid_detail["payment_summary"]["status"], "paid")
        self.assertIsNotNone(paid_detail["payment"])
        self.assertIsNotNone(paid_detail["invoice"])

        order_row = BizOrder.query.filter_by(order_code=order_code).first()
        summary = payment_summary_for_order(order_row)
        self.assertEqual(summary["status"], "paid")
        self.assertIn("cash", summary["payment_methods_supported"])

        # Fresh unpaid order for HTTP overpay / collect
        order2 = biz.create_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[test.id],
            actor=self.user.email,
        )
        biz.submit_order_for_payment(order2.order_code, actor=self.user.email)
        biz.create_invoice_from_order(order2.order_code, actor=self.user.email)
        db.session.commit()
        order_code2 = order2.order_code
        total2 = float(order2.total_amount)

        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["role"] = self.user.role
            sess["email"] = self.user.email

        over = client.post(
            f"/api/v1/reception/workspace/orders/{order_code2}/payment",
            json={"payment_method": "cash", "amount": total2 + 1},
            headers={"Idempotency-Key": f"HTTP-{uuid.uuid4().hex[:8]}"},
        )
        self.assertEqual(over.status_code, 400)

        ok_key = f"HTTP-OK-{uuid.uuid4().hex[:8]}"
        ok = client.post(
            f"/api/v1/reception/workspace/orders/{order_code2}/payment",
            json={"payment_method": "qr", "amount": total2},
            headers={"Idempotency-Key": ok_key},
        )
        self.assertEqual(ok.status_code, 200)
        body = ok.get_json()
        self.assertTrue(body.get("success"))
        self.assertEqual(body["data"]["payment_summary"]["status"], "paid")
        self.assertEqual(body["data"]["payment"]["receipt_number"], ok_key)

        replay_http = client.post(
            f"/api/v1/reception/workspace/orders/{order_code2}/payment",
            json={"payment_method": "qr", "amount": total2},
            headers={"Idempotency-Key": ok_key},
        )
        self.assertEqual(replay_http.status_code, 200)
        self.assertTrue(replay_http.get_json()["data"].get("idempotent_replay"))

        got = client.get(f"/api/v1/reception/workspace/orders/{order_code2}")
        self.assertEqual(got.status_code, 200)
        self.assertEqual(got.get_json()["data"]["payment_summary"]["status"], "paid")

    def test_duplicate_warnings_empty(self):
        self.assertEqual(duplicate_warnings(phone="0000000000"), [])

    def test_milestone3_barcode_reprint_and_requisition(self):
        """Paid-only documents; stable reprint; requisition HTML."""
        from app.models.test_catalog import TestCatalog
        from app.reception_workspace.service import (
            collect_payment,
            generate_barcodes,
            render_request_form,
            ReceptionWorkspaceError,
        )

        phone = f"0912{uuid.uuid4().hex[:6]}"
        patient = biz.create_patient(
            full_name="M3 DOCUMENTS PATIENT",
            phone=phone,
            patient_code=f"P-M3-{uuid.uuid4().hex[:6].upper()}",
            actor=self.user.email,
        )
        db.session.commit()
        test = TestCatalog.query.first()
        self.assertIsNotNone(test)
        order = biz.create_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[test.id],
            actor=self.user.email,
        )
        biz.submit_order_for_payment(order.order_code, actor=self.user.email)
        biz.create_invoice_from_order(order.order_code, actor=self.user.email)
        db.session.commit()
        order_code = order.order_code
        total = float(order.total_amount)

        with self.assertRaises(ReceptionWorkspaceError):
            generate_barcodes(order_code)

        collect_payment(
            order_code,
            payment_method="cash",
            amount=total,
            idempotency_key=f"RCT-M3-{uuid.uuid4().hex[:6]}",
            actor=self.user.email,
        )
        db.session.commit()

        first = generate_barcodes(order_code)
        self.assertTrue(first["patient_qr"].startswith("dxcon:patient:"))
        self.assertEqual(first["order_barcode"], f"BC-{order_code}")
        second = generate_barcodes(order_code)
        self.assertEqual(first["order_barcode"], second["order_barcode"])
        self.assertEqual(first["patient_qr"], second["patient_qr"])
        self.assertEqual(
            [s["barcode"] for s in first["sample_barcodes"]],
            [s["barcode"] for s in second["sample_barcodes"]],
        )
        # Payment may already set order.barcode_value; second call is always a reprint.
        self.assertTrue(second.get("reprint"))

        form = render_request_form(order_code)
        self.assertIn("html", form)
        self.assertIn(order_code, form["html"])
        self.assertEqual(form["barcodes"]["order_barcode"], first["order_barcode"])

        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["role"] = self.user.role
            sess["email"] = self.user.email
        barcode_resp = client.get(f"/api/v1/reception/workspace/orders/{order_code}/barcode")
        self.assertEqual(barcode_resp.status_code, 200)
        self.assertEqual(barcode_resp.get_json()["data"]["order_barcode"], first["order_barcode"])
        form_resp = client.get(f"/api/v1/reception/workspace/orders/{order_code}/request-form")
        self.assertEqual(form_resp.status_code, 200)
        self.assertIn("html", form_resp.get_json()["data"])

    def test_milestone4_lab_handoff_queue_and_idempotent(self):
        """Paid+docs → lab_received; unpaid/docs reject; duplicate idempotent; lab queue."""
        from app.models.biz_order import BizCollection, BizOrder
        from app.models.test_catalog import TestCatalog
        from app.reception_workspace.service import (
            ReceptionWorkspaceError,
            collect_payment,
            generate_barcodes,
            get_lab_handoff_status,
            handoff_to_laboratory,
            render_request_form,
        )

        phone = f"0913{uuid.uuid4().hex[:6]}"
        patient = biz.create_patient(
            full_name="M4 HANDOFF PATIENT",
            phone=phone,
            patient_code=f"P-M4-{uuid.uuid4().hex[:6].upper()}",
            actor=self.user.email,
        )
        db.session.commit()
        test = TestCatalog.query.first()
        self.assertIsNotNone(test)

        unpaid = biz.create_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[test.id],
            actor=self.user.email,
        )
        biz.submit_order_for_payment(unpaid.order_code, actor=self.user.email)
        biz.create_invoice_from_order(unpaid.order_code, actor=self.user.email)
        db.session.commit()
        with self.assertRaisesRegex(ReceptionWorkspaceError, "paid|Specimen|Requisition"):
            handoff_to_laboratory(unpaid.order_code, actor=self.user.email)

        order = biz.create_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[test.id],
            actor=self.user.email,
        )
        biz.submit_order_for_payment(order.order_code, actor=self.user.email)
        biz.create_invoice_from_order(order.order_code, actor=self.user.email)
        db.session.commit()
        order_code = order.order_code
        total = float(order.total_amount)

        collect_payment(
            order_code,
            payment_method="cash",
            amount=total,
            idempotency_key=f"RCT-M4-{uuid.uuid4().hex[:6]}",
            actor=self.user.email,
        )
        db.session.commit()

        # Paid but missing documents path is covered by generate_barcodes/requisition
        # being required inside handoff — call after docs exist.
        barcodes = generate_barcodes(order_code)
        self.assertTrue(barcodes.get("sample_barcodes"))
        form = render_request_form(order_code)
        self.assertTrue((form.get("html") or "").strip())

        first = handoff_to_laboratory(
            order_code,
            laboratory_name="Central Laboratory",
            laboratory_id="lab-central",
            actor=self.user.email,
        )
        db.session.commit()
        self.assertEqual(first["order_status"], "lab_received")
        self.assertTrue(first.get("handed_off"))
        self.assertFalse(first.get("idempotent_replay"))
        self.assertEqual(first["laboratory"]["name"], "Central Laboratory")
        self.assertEqual(first["laboratory"]["id"], "lab-central")
        self.assertIsNotNone(first.get("queue_reference"))
        self.assertIsNotNone(first.get("accepted_at"))

        order_row = BizOrder.query.filter_by(order_code=order_code).first()
        collections = BizCollection.query.filter_by(order_id=order_row.id).all()
        self.assertEqual(len(collections), 1)

        incoming = biz.list_lab_incoming(limit=50)
        self.assertTrue(any(row["order_code"] == order_code for row in incoming))
        match = next(row for row in incoming if row["order_code"] == order_code)
        self.assertEqual(match["status"], "lab_received")
        self.assertEqual(match["accession_number"], first["queue_reference"])

        replay = handoff_to_laboratory(
            order_code,
            laboratory_name="Central Laboratory",
            actor=self.user.email,
        )
        db.session.commit()
        self.assertTrue(replay.get("idempotent_replay"))
        self.assertEqual(replay["order_status"], "lab_received")
        self.assertEqual(replay["queue_reference"], first["queue_reference"])
        self.assertEqual(
            BizCollection.query.filter_by(order_id=order_row.id).count(),
            1,
        )

        status = get_lab_handoff_status(order_code)
        self.assertTrue(status.get("handed_off"))
        self.assertEqual(status["order_status"], "lab_received")
        self.assertEqual(status["queue_reference"], first["queue_reference"])

        # Resume after create_collection_after_payment (sampling) still lands once.
        order2 = biz.create_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[test.id],
            actor=self.user.email,
        )
        biz.submit_order_for_payment(order2.order_code, actor=self.user.email)
        biz.create_invoice_from_order(order2.order_code, actor=self.user.email)
        db.session.commit()
        collect_payment(
            order2.order_code,
            payment_method="qr",
            amount=float(order2.total_amount),
            idempotency_key=f"RCT-M4B-{uuid.uuid4().hex[:6]}",
            actor=self.user.email,
        )
        db.session.commit()
        generate_barcodes(order2.order_code)
        render_request_form(order2.order_code)
        from app.reception_workspace.service import create_collection_after_payment

        create_collection_after_payment(order2.order_code, actor=self.user.email)
        db.session.commit()
        mid = BizOrder.query.filter_by(order_code=order2.order_code).first()
        self.assertEqual(mid.status, "sampling")
        resumed = handoff_to_laboratory(order2.order_code, actor=self.user.email)
        db.session.commit()
        self.assertEqual(resumed["order_status"], "lab_received")
        self.assertEqual(
            BizCollection.query.filter_by(order_id=mid.id).count(),
            1,
        )

        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["role"] = self.user.role
            sess["email"] = self.user.email

        post = client.post(
            f"/api/v1/reception/workspace/orders/{order_code}/lab-handoff",
            json={"laboratory_name": "Central Laboratory"},
        )
        self.assertEqual(post.status_code, 200)
        self.assertTrue(post.get_json()["data"].get("idempotent_replay"))
        self.assertEqual(post.get_json()["data"]["order_status"], "lab_received")

        get_status = client.get(
            f"/api/v1/reception/workspace/orders/{order_code}/lab-handoff"
        )
        self.assertEqual(get_status.status_code, 200)
        self.assertTrue(get_status.get_json()["data"].get("handed_off"))

        unpaid_http = client.post(
            f"/api/v1/reception/workspace/orders/{unpaid.order_code}/lab-handoff",
            json={},
        )
        self.assertEqual(unpaid_http.status_code, 400)

        missing = client.post(
            "/api/v1/reception/workspace/orders/DOES-NOT-EXIST-M4/lab-handoff",
            json={},
        )
        self.assertEqual(missing.status_code, 404)

        # Permission denial — role not in reception write set.
        other = User(
            email=f"doctor-{uuid.uuid4().hex[:6]}@test.local",
            role="DOCTOR",
            password_hash="x",
            is_active=True,
        )
        db.session.add(other)
        db.session.commit()
        denied = self.app.test_client()
        with denied.session_transaction() as sess:
            sess["user_id"] = other.id
            sess["role"] = other.role
            sess["email"] = other.email
        forbid = denied.post(
            f"/api/v1/reception/workspace/orders/{order_code}/lab-handoff",
            json={},
        )
        self.assertIn(forbid.status_code, {401, 403})

    def test_reception_ui_route(self):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["role"] = self.user.role
            sess["email"] = self.user.email
        resp = client.get("/app/reception")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Reception Workspace", resp.data)


if __name__ == "__main__":
    unittest.main()
