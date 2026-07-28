"""Reception → Collector Queue routing — eligibility, isolation, idempotency."""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_rcq_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from app import create_app
from app.business_engine import service as biz
from app.core.statuses import COLLECTION_COLLECTED, COLLECTION_PENDING, COLLECTION_RECEIVED
from app.extensions.db import db
from app.models.biz_order import BizOrder
from app.models.sample_collection import SampleCollection
from app.models.test_catalog import TestCatalog
from app.models.user import User
from app.reception_workspace.service import create_reception_order, register_patient
from app.sample_collection_workspace.desk_bridge import (
    WALK_IN_COLLECTOR,
    ensure_desk_sample_collection,
    order_requires_specimen_collection,
)
from app.sample_collection_workspace.service import list_production_queue
from app.services.sample_collection_workflow import SampleCollectionWorkflowService


class ReceptionCollectorQueueRoutingTests(unittest.TestCase):
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
        self.collector = User(
            email=f"col-{uuid.uuid4().hex[:6]}@test.local",
            role="COLLECTOR",
            password_hash="x",
            is_active=True,
        )
        db.session.add_all([self.admin, self.collector])
        db.session.commit()
        self.blood = TestCatalog.query.filter_by(code="CBC").first() or TestCatalog.query.first()
        self.consult = TestCatalog(
            code=f"CONS-{uuid.uuid4().hex[:4].upper()}",
            name="Consult Only",
            category="Service",
            sample_type="consult",
            price=50000,
        )
        db.session.add(self.consult)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _session(self, user=None):
        user = user or self.admin
        with self.client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["email"] = user.email

    def _patient(self):
        return biz.create_patient(
            full_name="RCQ PATIENT",
            phone=f"0977{uuid.uuid4().hex[:6]}",
            patient_code=f"P-RCQ-{uuid.uuid4().hex[:6].upper()}",
            actor=self.admin.email,
        )

    def test_patient_only_not_in_collector_queue(self):
        before = list_production_queue(include_desk=True)["count"]
        register_patient(
            {
                "full_name": "PATIENT ONLY",
                "phone": f"0966{uuid.uuid4().hex[:6]}",
                "patient_code": f"P-ONLY-{uuid.uuid4().hex[:6].upper()}",
                "force": True,
            },
            actor=self.admin.email,
            force=True,
        )
        db.session.commit()
        after = list_production_queue(include_desk=True)["count"]
        self.assertEqual(before, after)
        self.assertEqual(SampleCollection.query.count(), 0)

    def test_order_requiring_collection_appears_in_queue(self):
        patient = self._patient()
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.blood.id],
            actor=self.admin.email,
            organization_id="org-desk-1",
        )
        db.session.commit()
        self.assertIn("sample_collection_id", result)
        sc_id = result["sample_collection_id"]
        sc = SampleCollection.query.get(sc_id)
        self.assertEqual(sc.status, COLLECTION_PENDING)
        self.assertIsNone(sc.marketplace_booking_id)
        self.assertEqual(sc.collector_name, WALK_IN_COLLECTOR)
        self.assertEqual(sc.collection_location, "Reception Desk")
        self.assertEqual(sc.partner_id, "org-desk-1")
        self.assertIn("source:desk", sc.notes or "")

        queue = list_production_queue(include_desk=True)
        row = next(i for i in queue["items"] if i["id"] == sc_id)
        self.assertEqual(row["source"], "desk")
        self.assertEqual(row["status"], "PENDING")
        self.assertEqual(row["collector_name"], WALK_IN_COLLECTOR)
        self.assertTrue(row["actionable"])

        self._session()
        api = self.client.get("/api/v1/sample-collections/queue")
        self.assertEqual(api.status_code, 200)
        ids = {i["id"] for i in api.get_json()["data"]["items"]}
        self.assertIn(sc_id, ids)

    def test_order_without_specimen_not_in_queue(self):
        patient = self._patient()
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.consult.id],
            actor=self.admin.email,
        )
        db.session.commit()
        self.assertNotIn("sample_collection_id", result)
        order = BizOrder.query.get(result["order"]["id"])
        self.assertFalse(order_requires_specimen_collection(order))
        self.assertEqual(SampleCollection.query.filter_by(order_id=result["order"]["id"]).count(), 0)

    def test_idempotent_no_duplicate_collections(self):
        patient = self._patient()
        first = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.blood.id],
            actor=self.admin.email,
        )
        db.session.commit()
        from app.models.biz_order import BizOrder

        order = BizOrder.query.get(first["order"]["id"])
        second = ensure_desk_sample_collection(order, organization_id="org-desk-1")
        third = ensure_desk_sample_collection(order)
        db.session.commit()
        self.assertEqual(first["sample_collection_id"], second.id)
        self.assertEqual(second.id, third.id)
        self.assertEqual(SampleCollection.query.filter_by(order_id=order.id).count(), 1)

    def test_organization_isolation_for_collector_role(self):
        patient = self._patient()
        a = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.blood.id],
            actor=self.admin.email,
            organization_id="org-A",
        )
        patient_b = self._patient()
        b = create_reception_order(
            patient_code=patient_b.patient_code,
            test_catalog_ids=[self.blood.id],
            actor=self.admin.email,
            organization_id="org-B",
        )
        db.session.commit()

        scoped = list_production_queue(
            include_desk=True,
            role="COLLECTOR",
            organization_id="org-A",
        )
        ids = {i["id"] for i in scoped["items"]}
        self.assertIn(a["sample_collection_id"], ids)
        self.assertNotIn(b["sample_collection_id"], ids)

        # SUPER_ADMIN without partner filter sees both
        all_items = list_production_queue(include_desk=True, role="SUPER_ADMIN")
        all_ids = {i["id"] for i in all_items["items"]}
        self.assertIn(a["sample_collection_id"], all_ids)
        self.assertIn(b["sample_collection_id"], all_ids)

    def test_status_filter_aliases_and_awaiting_default(self):
        patient = self._patient()
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.blood.id],
            actor=self.admin.email,
        )
        db.session.commit()
        sc_id = result["sample_collection_id"]

        awaiting = list_production_queue(include_desk=True)
        self.assertIn(sc_id, {i["id"] for i in awaiting["items"]})

        pending = list_production_queue(status="PENDING", include_desk=True)
        self.assertIn(sc_id, {i["id"] for i in pending["items"]})

        assigned = list_production_queue(status="ASSIGNED", include_desk=True)
        self.assertIn(sc_id, {i["id"] for i in assigned["items"]})

        # Simulate legacy assigned stored value still queue-eligible
        sc = SampleCollection.query.get(sc_id)
        sc.status = "assigned"
        db.session.commit()
        awaiting2 = list_production_queue(include_desk=True)
        row = next(i for i in awaiting2["items"] if i["id"] == sc_id)
        self.assertEqual(row["status"], "PENDING")  # normalized

    def test_include_desk_false_still_returns_desk_sample_collections(self):
        patient = self._patient()
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.blood.id],
            actor=self.admin.email,
        )
        db.session.commit()
        sc_id = result["sample_collection_id"]
        queue = list_production_queue(include_desk=False)
        self.assertIn(sc_id, {i["id"] for i in queue["items"]})

    def test_full_transition_verify_collect_dispatch_lab_arrival(self):
        patient = self._patient()
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.blood.id],
            actor=self.admin.email,
        )
        db.session.commit()
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
        SampleCollectionWorkflowService.dispatch_by_collection_id(
            sc_id, actor_email=self.admin.email
        )
        arrived, _ = SampleCollectionWorkflowService.receive_by_collection_id(
            sc_id, actor_email=self.admin.email
        )
        self.assertEqual(arrived.status, COLLECTION_RECEIVED)
        sc = SampleCollection.query.get(sc_id)
        self.assertEqual(sc.status, COLLECTION_RECEIVED)


if __name__ == "__main__":
    unittest.main()
