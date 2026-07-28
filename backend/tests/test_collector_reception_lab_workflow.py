"""E2E: Reception order → SampleCollection → Collector → Sample/Lab queues."""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_crl_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from app import create_app
from app.business_engine import service as biz
from app.core.statuses import (
    COLLECTION_CHECKED_IN,
    COLLECTION_COLLECTED,
    COLLECTION_IN_TRANSIT,
    COLLECTION_PENDING,
    COLLECTION_RECEIVED,
)
from app.extensions.db import db
from app.models.biz_order import BizCollection, BizLabQueueItem, BizSampleQueueItem
from app.models.sample_collection import SampleCollection
from app.models.test_catalog import TestCatalog
from app.models.user import User
from app.reception_workspace.service import create_reception_order
from app.sample_collection_workspace.desk_bridge import (
    ensure_desk_sample_collection,
    normalize_collection_status,
)
from app.sample_collection_workspace.service import collect_from_queue, list_production_queue
from app.services.sample_collection_workflow import SampleCollectionWorkflowService


class CollectorReceptionLabWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()
        biz.ensure_test_catalog_seed()
        self.admin = User(
            email=f"sa-{uuid.uuid4().hex[:6]}@test.local",
            role="SUPER_ADMIN",
            password_hash="x",
            is_active=True,
        )
        db.session.add(self.admin)
        db.session.commit()
        self.test = TestCatalog.query.first()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _session(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.admin.id
            sess["role"] = self.admin.role
            sess["email"] = self.admin.email

    def _create_reception_order(self):
        patient = biz.create_patient(
            full_name="CRL WORKFLOW PATIENT",
            phone=f"0988{uuid.uuid4().hex[:6]}",
            patient_code=f"P-CRL-{uuid.uuid4().hex[:6].upper()}",
            actor=self.admin.email,
        )
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.test.id],
            actor=self.admin.email,
        )
        db.session.commit()
        return result

    def test_reception_order_creates_sample_collection(self):
        result = self._create_reception_order()
        order = result["order"]
        self.assertIn("sample_collection_id", result)
        sc = SampleCollection.query.get(result["sample_collection_id"])
        self.assertIsNotNone(sc)
        self.assertEqual(sc.order_id, order["id"])
        self.assertIsNone(sc.marketplace_booking_id)
        self.assertEqual(sc.status, COLLECTION_PENDING)
        self.assertIn("source:desk", sc.notes or "")

    def test_idempotent_ensure_desk_sample_collection(self):
        result = self._create_reception_order()
        order_id = result["order"]["id"]
        from app.models.biz_order import BizOrder

        order = BizOrder.query.get(order_id)
        first = ensure_desk_sample_collection(order)
        second = ensure_desk_sample_collection(order)
        db.session.commit()
        self.assertEqual(first.id, second.id)
        count = SampleCollection.query.filter_by(order_id=order_id).count()
        self.assertEqual(count, 1)

    def test_new_collection_appears_in_collector_queue(self):
        result = self._create_reception_order()
        sc_id = result["sample_collection_id"]
        queue = list_production_queue(include_desk=True)
        ids = {item["id"] for item in queue["items"]}
        self.assertIn(sc_id, ids)
        row = next(item for item in queue["items"] if item["id"] == sc_id)
        self.assertEqual(row["source"], "desk")
        self.assertEqual(row["status"], "PENDING")
        self.assertTrue(row.get("actionable"))

    def test_pending_assigned_normalization(self):
        self.assertEqual(normalize_collection_status("assigned"), "PENDING")
        self.assertEqual(normalize_collection_status("ASSIGNED"), "PENDING")
        self.assertEqual(
            normalize_collection_status(
                "PENDING",
                patient_verified=True,
                order_verified=True,
            ),
            "VERIFIED",
        )
        self.assertEqual(normalize_collection_status("RECEIVED"), "ARRIVED_AT_LAB")
        self.assertEqual(normalize_collection_status("delivered"), "ARRIVED_AT_LAB")

    def test_desk_row_actionable_via_api(self):
        result = self._create_reception_order()
        sc_id = result["sample_collection_id"]
        self._session()
        resp = self.client.get("/api/v1/sample-collections/queue")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertTrue(body["success"])
        row = next(i for i in body["data"]["items"] if i["id"] == sc_id)
        self.assertEqual(row["source"], "desk")
        self.assertTrue(row["actionable"])
        detail = self.client.get(f"/api/v1/sample-collections/{sc_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.get_json()["data"]["source"], "desk")

    def test_full_desk_workflow_transitions_and_queues(self):
        result = self._create_reception_order()
        order = result["order"]
        sc_id = result["sample_collection_id"]
        barcode = order.get("barcode_value") or f"BC-{order['order_code']}"

        # VERIFY
        verified = SampleCollectionWorkflowService.verify_identifiers(
            sc_id,
            patient_name=order["patient_name"],
            booking_code=order["order_code"],
            scanned_barcode=barcode,
            actor_email=self.admin.email,
        )
        self.assertTrue(verified.patient_verified)
        self.assertTrue(verified.order_verified)
        self.assertEqual(verified.status, COLLECTION_CHECKED_IN)

        # COLLECT
        collected, sample = SampleCollectionWorkflowService.record_collection_by_id(
            sc_id,
            scanned_barcode=barcode,
            specimen_type="BLOOD",
            require_barcode=True,
            patient_verified=True,
            order_verified=True,
            actor_email=self.admin.email,
        )
        self.assertEqual(collected.status, COLLECTION_COLLECTED)
        self.assertIsNotNone(sample.sample_code)

        self.assertEqual(
            BizSampleQueueItem.query.filter_by(order_id=order["id"]).count(),
            1,
        )
        item = BizSampleQueueItem.query.filter_by(order_id=order["id"]).first()
        self.assertEqual(item.stage, "collected")

        # TRANSPORT / DISPATCH
        dispatched, _ = SampleCollectionWorkflowService.dispatch_by_collection_id(
            sc_id,
            actor_email=self.admin.email,
        )
        self.assertEqual(dispatched.status, COLLECTION_IN_TRANSIT)
        db.session.refresh(item)
        item = BizSampleQueueItem.query.filter_by(order_id=order["id"]).first()
        self.assertEqual(item.stage, "transport")

        # LAB ARRIVAL
        arrived, _ = SampleCollectionWorkflowService.receive_by_collection_id(
            sc_id,
            actor_email=self.admin.email,
        )
        self.assertEqual(arrived.status, COLLECTION_RECEIVED)
        item = BizSampleQueueItem.query.filter_by(order_id=order["id"]).first()
        self.assertEqual(item.stage, "received")

        lab_item = BizLabQueueItem.query.filter_by(order_id=order["id"]).first()
        self.assertIsNotNone(lab_item)
        self.assertEqual(lab_item.stage, "waiting")

        # Normalized queue status
        queue = list_production_queue(status="ARRIVED_AT_LAB", include_desk=True)
        ids = {i["id"] for i in queue["items"]}
        self.assertIn(sc_id, ids)
        row = next(i for i in queue["items"] if i["id"] == sc_id)
        self.assertEqual(row["status"], "ARRIVED_AT_LAB")
        self.assertFalse(row["actionable"])

    def test_collect_from_queue_facade_desk(self):
        result = self._create_reception_order()
        order = result["order"]
        sc_id = result["sample_collection_id"]
        barcode = order.get("barcode_value") or f"BC-{order['order_code']}"
        SampleCollectionWorkflowService.verify_identifiers(
            sc_id,
            patient_name=order["patient_name"],
            booking_code=order["order_code"],
            actor_email=self.admin.email,
        )
        payload = collect_from_queue(
            sc_id,
            {
                "scanned_barcode": barcode,
                "specimen_type": "BLOOD",
                "require_barcode": True,
            },
            actor=self.admin.email,
        )
        self.assertEqual(payload["collection"]["status"], COLLECTION_COLLECTED)
        self.assertIn("sample_tracking", payload)

    def test_api_collection_dispatch_and_lab_arrive(self):
        result = self._create_reception_order()
        order = result["order"]
        sc_id = result["sample_collection_id"]
        barcode = order.get("barcode_value") or f"BC-{order['order_code']}"
        SampleCollectionWorkflowService.verify_identifiers(
            sc_id,
            patient_name=order["patient_name"],
            booking_code=order["order_code"],
            actor_email=self.admin.email,
        )
        SampleCollectionWorkflowService.record_collection_by_id(
            sc_id,
            scanned_barcode=barcode,
            require_barcode=True,
            actor_email=self.admin.email,
        )
        self._session()
        dispatch = self.client.post(
            f"/api/v1/sample-collections/{sc_id}/dispatch",
            json={"note": "desk dispatch"},
        )
        self.assertEqual(dispatch.status_code, 200, dispatch.get_json())
        arrive = self.client.post(
            f"/api/v1/sample-collections/{sc_id}/lab-arrive",
            json={"note": "desk lab"},
        )
        self.assertEqual(arrive.status_code, 200, arrive.get_json())
        body = arrive.get_json()["data"]
        self.assertEqual(body["collection"]["status"], COLLECTION_RECEIVED)
        # Detail endpoint normalizes RECEIVED → ARRIVED_AT_LAB
        detail = self.client.get(f"/api/v1/sample-collections/{sc_id}")
        self.assertEqual(detail.get_json()["data"]["status"], "ARRIVED_AT_LAB")
        self.assertIsNotNone(BizLabQueueItem.query.filter_by(order_id=order["id"]).first())


if __name__ == "__main__":
    unittest.main()
