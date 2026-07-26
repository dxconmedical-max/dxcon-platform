"""Laboratory Queue tests — enqueue, advance, priority, stats, refresh."""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_labq_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from app import create_app
from app.business_engine import service as biz
from app.extensions.db import db
from app.models.audit_log import AuditLog
from app.models.test_catalog import TestCatalog
from app.models.user import User
from app.reception_workspace.errors import ReceptionWorkspaceError
from app.reception_workspace.lab_queue_engine import (
    STAGE_COMPLETED,
    STAGE_PROCESSING,
    STAGE_VERIFIED,
    STAGE_WAITING,
    advance_lab_queue,
    lab_queue_dashboard,
    lab_queue_refresh,
    lab_queue_statistics,
    set_lab_queue_priority,
)
from app.reception_workspace.service import collect_payment, generate_barcodes, handoff_to_laboratory


class LabQueueEngineTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()
        biz.ensure_test_catalog_seed()
        user = User(
            email=f"lq-{uuid.uuid4().hex[:6]}@test.local",
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

    def _paid_barcoded_order(self):
        patient = biz.create_patient(
            full_name="LABQ PATIENT",
            phone=f"0901{uuid.uuid4().hex[:6]}",
            patient_code=f"P-LQ-{uuid.uuid4().hex[:6].upper()}",
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
            idempotency_key=f"LQ-{uuid.uuid4().hex[:8]}",
            actor=self.user.email,
        )
        db.session.commit()
        generate_barcodes(order.order_code)
        db.session.commit()
        return order

    def test_handoff_enqueue_advance_priority_stats(self):
        order = self._paid_barcoded_order()
        handoff = handoff_to_laboratory(order.order_code, actor=self.user.email)
        db.session.commit()
        self.assertIn("lab_queue", handoff)
        self.assertEqual(handoff["lab_queue"]["stage"], STAGE_WAITING)

        urgent = set_lab_queue_priority(
            order.order_code, priority="urgent", actor=self.user.email
        )
        db.session.commit()
        self.assertEqual(urgent["priority"], "urgent")

        processing = advance_lab_queue(
            order.order_code, to_stage=STAGE_PROCESSING, actor=self.user.email
        )
        db.session.commit()
        self.assertEqual(processing["stage"], STAGE_PROCESSING)
        self.assertIsNotNone(processing["started_at"])

        completed = advance_lab_queue(
            order.order_code, to_stage=STAGE_COMPLETED, actor=self.user.email
        )
        db.session.commit()
        self.assertEqual(completed["stage"], STAGE_COMPLETED)

        verified = advance_lab_queue(
            order.order_code, to_stage=STAGE_VERIFIED, actor=self.user.email
        )
        db.session.commit()
        self.assertEqual(verified["stage"], STAGE_VERIFIED)
        self.assertEqual(verified["verified_by"], self.user.email)

        with self.assertRaises(ReceptionWorkspaceError):
            advance_lab_queue(order.order_code, to_stage=STAGE_PROCESSING)

        with self.assertRaises(ReceptionWorkspaceError):
            set_lab_queue_priority(order.order_code, priority="high")

        stats = lab_queue_statistics()
        self.assertEqual(stats["verified"], 1)
        self.assertEqual(stats["total_queued"], 1)
        self.assertIn("waiting", stats["pipeline"])

        dash = lab_queue_dashboard()
        self.assertTrue(dash["version"] > 0)
        self.assertEqual(len(dash["items"]), 1)

        refresh = lab_queue_refresh(version=dash["version"])
        self.assertFalse(refresh["changed"])

        audits = AuditLog.query.filter(AuditLog.action.like("%lab_queue%")).all()
        self.assertGreaterEqual(len(audits), 1)

    def test_api_dashboard_enqueue_advance_refresh(self):
        order = self._paid_barcoded_order()
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["role"] = self.user.role
            sess["email"] = self.user.email

        enq = client.post(
            f"/api/v1/reception/workspace/lab-queue/orders/{order.order_code}/enqueue",
            json={"priority": "high"},
        )
        self.assertEqual(enq.status_code, 200)
        self.assertEqual(enq.get_json()["data"]["lab_queue"]["priority"], "high")

        dash = client.get("/api/v1/reception/workspace/lab-queue")
        self.assertEqual(dash.status_code, 200)
        body = dash.get_json()["data"]
        self.assertGreaterEqual(body["statistics"]["waiting"], 1)
        version = body["version"]

        adv = client.post(
            f"/api/v1/reception/workspace/lab-queue/orders/{order.order_code}/advance",
            json={"to": "processing"},
        )
        self.assertEqual(adv.status_code, 200)
        self.assertEqual(adv.get_json()["data"]["stage"], "processing")

        stats = client.get("/api/v1/reception/workspace/lab-queue/stats")
        self.assertEqual(stats.status_code, 200)
        self.assertGreaterEqual(stats.get_json()["data"]["processing"], 1)

        refresh = client.get(
            f"/api/v1/reception/workspace/lab-queue/refresh?version={version}"
        )
        self.assertEqual(refresh.status_code, 200)
        self.assertTrue(refresh.get_json()["data"]["changed"])


if __name__ == "__main__":
    unittest.main()
