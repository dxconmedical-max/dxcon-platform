"""Integration: Reception HOME → Field Requests (REQUESTED) → Assign → Collector Queue (ASSIGNED) → collect."""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_home_queue_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from app import create_app
from app.business_engine import service as biz
from app.extensions.db import db
from app.models.home_collection import HomeCollection
from app.models.sample_collection import SampleCollection
from app.models.test_catalog import TestCatalog
from app.models.user import User
from app.reception_workspace.service import create_reception_order
from app.sample_collection_workspace.collection_domain import (
    MODE_HOME_COLLECTION,
    ST_ASSIGNED,
    ST_COLLECTED,
    ST_REQUESTED,
    ST_VERIFIED,
)
from app.sample_collection_workspace.collection_routing import (
    assign_collector,
    ensure_sample_collection_from_home_collection,
    list_field_collector_queue,
    list_home_field_requests,
)
from app.services.sample_collection_workflow import SampleCollectionWorkflowService


class ReceptionHomeToCollectorQueueTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()
        biz.ensure_test_catalog_seed()
        self.reception = User(
            email=f"rx-{uuid.uuid4().hex[:6]}@test.local",
            role="RECEPTION",
            password_hash="x",
            is_active=True,
        )
        self.collector = User(
            email=f"col-{uuid.uuid4().hex[:6]}@test.local",
            role="COLLECTOR",
            password_hash="x",
            is_active=True,
        )
        db.session.add_all([self.reception, self.collector])
        db.session.commit()
        self.cbc = TestCatalog.query.filter_by(code="CBC").first() or TestCatalog.query.first()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _login(self, user: User):
        with self.client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["email"] = user.email

    def test_home_request_field_board_then_assign_then_collector_queue(self):
        patient = biz.create_patient(
            full_name="HOME Queue Patient",
            phone=f"09{uuid.uuid4().hex[:8]}",
            patient_code=f"P-HQ-{uuid.uuid4().hex[:4].upper()}",
            actor=self.reception.email,
        )
        created = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.cbc.id],
            collection_mode=MODE_HOME_COLLECTION,
            pickup={
                "pickup_address": "12 Integration St",
                "pickup_province": "HCM",
                "pickup_district": "Q1",
                "contact_person": patient.full_name,
                "contact_phone": "0911222333",
                "requested_date": "2026-08-12",
                "requested_time_window": "09:00-11:00",
                "specimen_type": "BLOOD",
                "priority": "ROUTINE",
            },
            actor=self.reception.email,
            organization_id="org-hq",
        )
        db.session.commit()

        sc_id = created["sample_collection_id"]
        rows = SampleCollection.query.filter_by(order_id=created["order"]["id"]).all()
        self.assertEqual(len(rows), 1)
        sc = rows[0]
        self.assertEqual(sc.status, ST_REQUESTED)
        self.assertEqual(sc.collection_mode, MODE_HOME_COLLECTION)

        field = list_home_field_requests()
        self.assertIn(sc_id, {i["id"] for i in field["items"]})
        self.assertEqual(
            next(i for i in field["items"] if i["id"] == sc_id)["status"],
            ST_REQUESTED,
        )

        # Collector queue must NOT show unassigned REQUESTED jobs
        before_assign = list_field_collector_queue(role="COLLECTOR", organization_id="org-hq")
        self.assertNotIn(sc_id, {i["id"] for i in before_assign["items"]})

        self._login(self.reception)
        fr = self.client.get("/api/v1/reception/field-requests")
        self.assertEqual(fr.status_code, 200, fr.get_json())
        self.assertIn(sc_id, {i["id"] for i in fr.get_json()["data"]["items"]})

        assign_collector(
            sc_id,
            collector_id=self.collector.id,
            collector_name="Queue Collector",
            actor=self.reception.email,
        )
        db.session.commit()
        sc = SampleCollection.query.get(sc_id)
        self.assertEqual(sc.status, ST_ASSIGNED)

        # After assign, REQUESTED board drops it; Collector Queue shows ASSIGNED
        field_after = list_home_field_requests()
        self.assertNotIn(sc_id, {i["id"] for i in field_after["items"]})

        queue = list_field_collector_queue(role="COLLECTOR", organization_id="org-hq")
        self.assertIn(sc_id, {i["id"] for i in queue["items"]})
        self.assertEqual(next(i for i in queue["items"] if i["id"] == sc_id)["status"], ST_ASSIGNED)

        self._login(self.collector)
        cq = self.client.get("/api/v1/collector/queue")
        self.assertEqual(cq.status_code, 200, cq.get_json())
        self.assertIn(sc_id, {i["id"] for i in cq.get_json()["data"]["items"]})

        order_code = created["order"]["order_code"]
        barcode = created["order"].get("barcode_value") or f"BC-{order_code}"
        SampleCollectionWorkflowService.verify_identifiers(
            sc_id,
            patient_name=created["order"]["patient_name"],
            booking_code=order_code,
            actor_email=self.collector.email,
        )
        self.assertEqual(SampleCollection.query.get(sc_id).status, ST_VERIFIED)

        SampleCollectionWorkflowService.record_collection_by_id(
            sc_id,
            scanned_barcode=barcode,
            require_barcode=True,
            actor_email=self.collector.email,
        )
        db.session.commit()
        self.assertEqual(SampleCollection.query.get(sc_id).status, ST_COLLECTED)

    def test_legacy_home_collection_creates_sample_collection(self):
        patient = biz.create_patient(
            full_name="Legacy Home",
            phone=f"09{uuid.uuid4().hex[:8]}",
            patient_code=f"P-LG-{uuid.uuid4().hex[:4].upper()}",
            actor=self.reception.email,
        )
        home = HomeCollection(
            patient_id=patient.patient_code,
            address="99 Legacy Rd",
            scheduled_time="2026-08-15 10:00",
            status="REQUESTED",
        )
        db.session.add(home)
        db.session.flush()
        sc = ensure_sample_collection_from_home_collection(home, actor="test")
        db.session.commit()
        self.assertEqual(sc.collection_mode, MODE_HOME_COLLECTION)
        self.assertEqual(sc.status, ST_REQUESTED)
        self.assertIn(sc.id, {i["id"] for i in list_home_field_requests()["items"]})


if __name__ == "__main__":
    unittest.main()
