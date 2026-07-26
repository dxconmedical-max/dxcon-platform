"""Sample Queue tests — enqueue, advance, tracking, history, audit, refresh."""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_smq_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from app import create_app
from app.business_engine import service as biz
from app.extensions.db import db
from app.models.audit_log import AuditLog
from app.models.biz_order import BizSampleQueueEvent
from app.models.test_catalog import TestCatalog
from app.models.user import User
from app.reception_workspace.errors import ReceptionWorkspaceError
from app.reception_workspace.sample_queue_engine import (
    STAGE_COMPLETED,
    STAGE_LABORATORY,
    STAGE_RECEIVED,
    STAGE_SORTING,
    STAGE_TRANSPORT,
    advance_sample_queue,
    ensure_sample_queue_item,
    get_sample_queue_history,
    sample_queue_dashboard,
    sample_queue_refresh,
    track_sample,
    update_sample_tracking,
)
from app.reception_workspace.service import collect_payment, generate_barcodes


class SampleQueueEngineTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()
        biz.ensure_test_catalog_seed()
        user = User(
            email=f"sq-{uuid.uuid4().hex[:6]}@test.local",
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

    def _paid_with_collection(self):
        patient = biz.create_patient(
            full_name="SAMPLE Q PATIENT",
            phone=f"0922{uuid.uuid4().hex[:6]}",
            patient_code=f"P-SQ-{uuid.uuid4().hex[:6].upper()}",
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
            idempotency_key=f"SQ-{uuid.uuid4().hex[:8]}",
            actor=self.user.email,
        )
        db.session.commit()
        generate_barcodes(order.order_code)
        biz.create_collection_job(
            order.order_code,
            collector_name="Desk",
            pickup_address="Reception",
            actor=self.user.email,
        )
        db.session.commit()
        return order

    def test_workflow_history_tracking_audit(self):
        order = self._paid_with_collection()
        entered = ensure_sample_queue_item(order.order_code, actor=self.user.email)
        db.session.commit()
        self.assertEqual(entered["stage"], "collected")
        self.assertTrue(entered["history"])

        for stage in (
            STAGE_TRANSPORT,
            STAGE_RECEIVED,
            STAGE_SORTING,
            STAGE_LABORATORY,
            STAGE_COMPLETED,
        ):
            advanced = advance_sample_queue(
                order.order_code, to_stage=stage, actor=self.user.email
            )
            db.session.commit()
            self.assertEqual(advanced["stage"], stage)

        with self.assertRaises(ReceptionWorkspaceError):
            advance_sample_queue(order.order_code, to_stage=STAGE_TRANSPORT)

        hist = get_sample_queue_history(order.order_code)
        self.assertGreaterEqual(len(hist), 6)
        self.assertEqual(BizSampleQueueEvent.query.count(), len(hist))

        tracked = update_sample_tracking(
            order.order_code,
            location="Cold room A",
            note="custody check",
            actor=self.user.email,
        )
        db.session.commit()
        self.assertEqual(tracked["location"], "Cold room A")

        snap = track_sample(order.order_code)
        self.assertTrue(snap["on_queue"])
        self.assertEqual(snap["stage"], STAGE_COMPLETED)

        dash = sample_queue_dashboard()
        self.assertEqual(dash["statistics"]["completed"], 1)
        refresh = sample_queue_refresh(version=dash["version"])
        self.assertFalse(refresh["changed"])

        audits = AuditLog.query.filter(AuditLog.action.like("%sample_queue%")).all()
        self.assertGreaterEqual(len(audits), 1)

    def test_api_enqueue_advance_track_history_refresh(self):
        order = self._paid_with_collection()
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["role"] = self.user.role
            sess["email"] = self.user.email

        enq = client.post(
            f"/api/v1/reception/workspace/sample-queue/orders/{order.order_code}/enqueue",
            json={"location": "Desk"},
        )
        self.assertEqual(enq.status_code, 200)
        self.assertEqual(enq.get_json()["data"]["stage"], "collected")

        dash = client.get("/api/v1/reception/workspace/sample-queue")
        self.assertEqual(dash.status_code, 200)
        version = dash.get_json()["data"]["version"]

        adv = client.post(
            f"/api/v1/reception/workspace/sample-queue/orders/{order.order_code}/advance",
            json={"to": "transport"},
        )
        self.assertEqual(adv.status_code, 200)
        self.assertEqual(adv.get_json()["data"]["stage"], "transport")

        track = client.get(
            f"/api/v1/reception/workspace/sample-queue/orders/{order.order_code}/track"
        )
        self.assertEqual(track.status_code, 200)
        self.assertTrue(track.get_json()["data"]["on_queue"])

        hist = client.get(
            f"/api/v1/reception/workspace/sample-queue/orders/{order.order_code}/history"
        )
        self.assertEqual(hist.status_code, 200)
        self.assertGreaterEqual(len(hist.get_json()["data"]["history"]), 2)

        refresh = client.get(
            f"/api/v1/reception/workspace/sample-queue/refresh?version={version}"
        )
        self.assertEqual(refresh.status_code, 200)
        self.assertTrue(refresh.get_json()["data"]["changed"])


if __name__ == "__main__":
    unittest.main()
