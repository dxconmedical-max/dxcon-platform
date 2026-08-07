"""Reception → SampleCollection → Collector/Desk → Lab workflow (merged hotfix + main)."""

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
    COLLECTION_COLLECTED,
    COLLECTION_IN_TRANSIT,
)
from app.extensions.db import db
from app.models.biz_order import BizLabQueueItem, BizSampleQueueItem
from app.models.sample_collection import SampleCollection
from app.models.test_catalog import TestCatalog
from app.models.user import User
from app.reception_workspace.service import create_reception_order
from app.sample_collection_workspace.collection_domain import (
    MODE_AT_RECEPTION,
    ST_ARRIVED_AT_LAB,
    ST_COLLECTED,
    ST_REQUESTED,
    ST_VERIFIED,
    normalize_status,
)
from app.sample_collection_workspace.collection_routing import (
    ensure_desk_sample_collection,
    list_reception_desk_queue,
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
            collection_mode=MODE_AT_RECEPTION,
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
        self.assertEqual(sc.collection_mode, MODE_AT_RECEPTION)
        self.assertEqual(sc.status, ST_REQUESTED)

    def test_idempotent_ensure_desk_sample_collection(self):
        result = self._create_reception_order()
        from app.models.biz_order import BizOrder

        order = BizOrder.query.get(result["order"]["id"])
        first = ensure_desk_sample_collection(order)
        second = ensure_desk_sample_collection(order)
        db.session.commit()
        self.assertEqual(first.id, second.id)
        self.assertEqual(SampleCollection.query.filter_by(order_id=order.id).count(), 1)

    def test_at_reception_in_desk_not_field_queue(self):
        result = self._create_reception_order()
        sc_id = result["sample_collection_id"]
        desk = list_reception_desk_queue()
        self.assertIn(sc_id, {item["id"] for item in desk["items"]})
        field = list_production_queue()
        self.assertNotIn(sc_id, {item["id"] for item in field["items"]})

    def test_status_normalization(self):
        self.assertEqual(normalize_status("assigned"), "ASSIGNED")
        self.assertEqual(normalize_status("PENDING"), "REQUESTED")
        self.assertEqual(normalize_status("CHECKED_IN"), "VERIFIED")
        self.assertEqual(normalize_status("RECEIVED"), "ARRIVED_AT_LAB")

    def test_desk_row_via_desk_collections_api(self):
        result = self._create_reception_order()
        sc_id = result["sample_collection_id"]
        self._session()
        resp = self.client.get("/api/v1/reception/workspace/desk-collections")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertTrue(body["success"])
        row = next(i for i in body["data"]["items"] if i["id"] == sc_id)
        self.assertEqual(row.get("collection_mode") or MODE_AT_RECEPTION, MODE_AT_RECEPTION)
        detail = self.client.get(f"/api/v1/sample-collections/{sc_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertIn(
            detail.get_json()["data"].get("source"),
            {"desk", "reception", MODE_AT_RECEPTION},
        )
    def test_full_desk_workflow_transitions_and_queues(self):
        result = self._create_reception_order()
        order = result["order"]
        sc_id = result["sample_collection_id"]
        barcode = order.get("barcode_value") or f"BC-{order['order_code']}"

        verified = SampleCollectionWorkflowService.verify_identifiers(
            sc_id,
            patient_name=order["patient_name"],
            booking_code=order["order_code"],
            scanned_barcode=barcode,
            actor_email=self.admin.email,
        )
        self.assertTrue(verified.patient_verified)
        self.assertTrue(verified.order_verified)
        self.assertEqual(normalize_status(verified.status), ST_VERIFIED)

        collected, sample = SampleCollectionWorkflowService.record_collection_by_id(
            sc_id,
            scanned_barcode=barcode,
            specimen_type="BLOOD",
            require_barcode=True,
            patient_verified=True,
            order_verified=True,
            actor_email=self.admin.email,
        )
        self.assertEqual(normalize_status(collected.status), ST_COLLECTED)
        self.assertIsNotNone(sample.sample_code)
        self.assertEqual(
            BizSampleQueueItem.query.filter_by(order_id=order["id"]).count(),
            1,
        )
        item = BizSampleQueueItem.query.filter_by(order_id=order["id"]).first()
        self.assertEqual(item.stage, "collected")

        dispatched, _ = SampleCollectionWorkflowService.dispatch_by_collection_id(
            sc_id,
            actor_email=self.admin.email,
        )
        self.assertIn(dispatched.status, {COLLECTION_IN_TRANSIT, "IN_TRANSIT"})
        item = BizSampleQueueItem.query.filter_by(order_id=order["id"]).first()
        self.assertEqual(item.stage, "transport")

        arrived, _ = SampleCollectionWorkflowService.receive_by_collection_id(
            sc_id,
            actor_email=self.admin.email,
        )
        self.assertEqual(normalize_status(arrived.status), ST_ARRIVED_AT_LAB)
        item = BizSampleQueueItem.query.filter_by(order_id=order["id"]).first()
        self.assertEqual(item.stage, "received")

        lab_item = BizLabQueueItem.query.filter_by(order_id=order["id"]).first()
        self.assertIsNotNone(lab_item)
        self.assertEqual(lab_item.stage, "waiting")

        sc = SampleCollection.query.get(sc_id)
        self.assertEqual(normalize_status(sc.status), ST_ARRIVED_AT_LAB)

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
        self.assertEqual(
            normalize_status(payload["collection"]["status"]),
            ST_COLLECTED,
        )
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
        self.assertEqual(
            normalize_status(body["collection"]["status"]),
            ST_ARRIVED_AT_LAB,
        )
        detail = self.client.get(f"/api/v1/sample-collections/{sc_id}")
        self.assertEqual(
            normalize_status(detail.get_json()["data"]["status"]),
            ST_ARRIVED_AT_LAB,
        )
        self.assertIsNotNone(BizLabQueueItem.query.filter_by(order_id=order["id"]).first())


if __name__ == "__main__":
    unittest.main()
