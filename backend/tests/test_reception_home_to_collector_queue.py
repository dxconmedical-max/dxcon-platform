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
    MODE_CLINIC_COLLECTION,
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
        self.reception_id = self.reception.id
        self.collector_id = self.collector.id
        self.reception_email = self.reception.email
        self.collector_email = self.collector.email
        cbc = TestCatalog.query.filter_by(code="CBC").first() or TestCatalog.query.first()
        self.cbc_id = cbc.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _login(self, user: User):
        if user is self.collector or getattr(user, "role", None) == "COLLECTOR":
            user_id, role, email = self.collector_id, "COLLECTOR", self.collector_email
        else:
            user_id, role, email = self.reception_id, "RECEPTION", self.reception_email
        with self.client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["role"] = role
            sess["email"] = email

    def _create_patient(self, label: str):
        return biz.create_patient(
            full_name=f"{label} Patient",
            phone=f"09{uuid.uuid4().hex[:8]}",
            patient_code=f"P-{label[:2].upper()}-{uuid.uuid4().hex[:4].upper()}",
            actor=self.reception_email,
        )

    def test_home_request_field_board_then_assign_then_collector_queue(self):
        patient = self._create_patient("HQ")
        created = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.cbc_id],
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
            actor=self.reception_email,
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
            collector_id=self.collector_id,
            collector_name="Queue Collector",
            actor=self.reception_email,
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
            actor_email=self.collector_email,
        )
        self.assertEqual(SampleCollection.query.get(sc_id).status, ST_VERIFIED)

        SampleCollectionWorkflowService.record_collection_by_id(
            sc_id,
            scanned_barcode=barcode,
            require_barcode=True,
            actor_email=self.collector_email,
        )
        db.session.commit()
        self.assertEqual(SampleCollection.query.get(sc_id).status, ST_COLLECTED)

    def test_http_home_create_field_board_id_assign_collector_queue(self):
        """Invariant: create HOME → one SC → field board same id → assign → collector queue."""
        patient = self._create_patient("HTTP")
        patient_code = patient.patient_code
        patient_name = patient.full_name
        db.session.commit()
        self._login(self.reception)

        created = self.client.post(
            "/api/v1/reception/workspace/orders",
            json={
                "patient_code": patient_code,
                "test_catalog_ids": [self.cbc_id],
                "collection_mode": MODE_HOME_COLLECTION,
                "pickup_address": "88 HTTP St",
                "pickup_province": "HCM",
                "pickup_district": "Q3",
                "contact_person": patient_name,
                "contact_phone": "0988776655",
                "requested_date": "2026-08-20",
                "requested_time_window": "10:00-12:00",
                "specimen_type": "BLOOD",
            },
        )
        self.assertEqual(created.status_code, 201, created.get_json())
        body = created.get_json()["data"]
        sc_id = body["sample_collection_id"]
        order_id = body["order"]["id"]
        self.assertTrue(sc_id)
        self.assertEqual(len(SampleCollection.query.filter_by(order_id=order_id).all()), 1)

        # Simulate new HTTP request (session teardown) before Field Requests / Assign.
        db.session.remove()
        self.assertIsNotNone(SampleCollection.query.get(sc_id))

        fr = self.client.get("/api/v1/reception/workspace/field-collection-requests")
        self.assertEqual(fr.status_code, 200, fr.get_json())
        items = fr.get_json()["data"]["items"]
        match = next(i for i in items if i["id"] == sc_id)
        self.assertEqual(match["sample_collection_id"], sc_id)
        self.assertEqual(match["order_id"], order_id)
        self.assertEqual(match["status"], ST_REQUESTED)

        db.session.remove()
        assigned = self.client.post(
            f"/api/v1/sample-collections/{sc_id}/assign",
            json={"collector_id": self.collector_id, "collector_name": "HTTP Collector"},
        )
        self.assertEqual(assigned.status_code, 200, assigned.get_json())
        sc = SampleCollection.query.get(sc_id)
        self.assertEqual(sc.collector_id, self.collector_id)
        self.assertEqual(sc.status, ST_ASSIGNED)

        # Assign also resolves when client mistakenly sends order_id.
        other = self._create_patient("ORD")
        other_code = other.patient_code
        other_name = other.full_name
        created2 = create_reception_order(
            patient_code=other_code,
            test_catalog_ids=[self.cbc_id],
            collection_mode=MODE_HOME_COLLECTION,
            pickup={
                "pickup_address": "1 Order Id St",
                "pickup_province": "HN",
                "pickup_district": "BK",
                "contact_person": other_name,
                "contact_phone": "0900111222",
                "requested_date": "2026-08-21",
                "requested_time_window": "08:00-09:00",
                "specimen_type": "BLOOD",
            },
            actor=self.reception_email,
        )
        db.session.commit()
        order2_id = created2["order"]["id"]
        sc2_id = created2["sample_collection_id"]
        db.session.remove()
        by_order = self.client.post(
            f"/api/v1/sample-collections/{order2_id}/assign",
            json={"collector_id": self.collector_id, "collector_name": "By Order"},
        )
        self.assertEqual(by_order.status_code, 200, by_order.get_json())
        self.assertEqual(SampleCollection.query.get(sc2_id).status, ST_ASSIGNED)

        self._login(self.collector)
        cq = self.client.get("/api/v1/collector/queue")
        self.assertEqual(cq.status_code, 200, cq.get_json())
        queue_ids = {i["id"] for i in cq.get_json()["data"]["items"]}
        self.assertIn(sc_id, queue_ids)
        self.assertIn(sc2_id, queue_ids)

    def test_http_clinic_create_field_board_then_assign(self):
        patient = self._create_patient("CLN")
        patient_code = patient.patient_code
        db.session.commit()
        self._login(self.reception)
        created = self.client.post(
            "/api/v1/reception/workspace/orders",
            json={
                "patient_code": patient_code,
                "test_catalog_ids": [self.cbc_id],
                "collection_mode": MODE_CLINIC_COLLECTION,
                "clinic_name": "District Clinic",
                "requested_date": "2026-08-22",
                "requested_time_window": "14:00-15:00",
                "specimen_type": "BLOOD",
            },
        )
        self.assertEqual(created.status_code, 201, created.get_json())
        sc_id = created.get_json()["data"]["sample_collection_id"]
        db.session.remove()

        fr = self.client.get("/api/v1/reception/workspace/field-collection-requests")
        self.assertIn(sc_id, {i["id"] for i in fr.get_json()["data"]["items"]})

        assigned = self.client.post(
            f"/api/v1/sample-collections/{sc_id}/assign",
            json={"collector_id": self.collector_id, "collector_name": "Clinic Col"},
        )
        self.assertEqual(assigned.status_code, 200, assigned.get_json())
        sc = SampleCollection.query.get(sc_id)
        self.assertEqual(sc.collection_mode, MODE_CLINIC_COLLECTION)
        self.assertEqual(sc.collector_id, self.collector_id)
        self.assertEqual(sc.status, ST_ASSIGNED)

    def test_legacy_home_collection_creates_sample_collection(self):
        patient = self._create_patient("LG")
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

    def test_field_requests_sync_commits_bridged_sample_collection_for_assign(self):
        """GET field-requests must persist bridged SC so Assign finds it after teardown."""
        patient = self._create_patient("SYNC")
        home = HomeCollection(
            patient_id=patient.patient_code,
            address="77 Sync Ave",
            scheduled_time="2026-08-18 09:00",
            status="REQUESTED",
        )
        db.session.add(home)
        db.session.commit()
        self.assertEqual(SampleCollection.query.count(), 0)

        self._login(self.reception)
        fr = self.client.get("/api/v1/reception/workspace/field-collection-requests")
        self.assertEqual(fr.status_code, 200, fr.get_json())
        items = fr.get_json()["data"]["items"]
        self.assertEqual(len(items), 1)
        sc_id = items[0]["id"]

        db.session.remove()
        self.assertIsNotNone(
            SampleCollection.query.get(sc_id),
            "bridged SampleCollection must be committed by field-requests list",
        )

        assigned = self.client.post(
            f"/api/v1/sample-collections/{sc_id}/assign",
            json={"collector_id": self.collector_id, "collector_name": "Sync Collector"},
        )
        self.assertEqual(assigned.status_code, 200, assigned.get_json())
        sc = SampleCollection.query.get(sc_id)
        self.assertEqual(sc.collector_id, self.collector_id)
        self.assertEqual(sc.status, ST_ASSIGNED)


if __name__ == "__main__":
    unittest.main()
