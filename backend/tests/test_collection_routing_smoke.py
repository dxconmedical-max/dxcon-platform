"""Production smoke: Reception HOME / AT_RECEPTION / CLINIC collection routing."""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_smoke_coll_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from app import create_app
from app.business_engine import service as biz
from app.extensions.db import db
from app.models.sample_collection import SampleCollection
from app.models.test_catalog import TestCatalog
from app.models.user import User
from app.reception_workspace.service import create_reception_order
from app.sample_collection_workspace.collection_domain import (
    MODE_AT_RECEPTION,
    MODE_CLINIC_COLLECTION,
    MODE_HOME_COLLECTION,
    ST_PENDING_ASSIGNMENT,
    ST_REQUESTED,
)
from app.sample_collection_workspace.collection_routing import (
    list_field_collector_queue,
    list_home_field_requests,
    list_reception_desk_queue,
)
from app.sample_collection_workspace.service import list_production_queue


class CollectionRoutingSmokeTests(unittest.TestCase):
    """Exact production smoke scenarios from product QA."""

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
            email=f"smoke-{uuid.uuid4().hex[:6]}@test.local",
            role="SUPER_ADMIN",
            password_hash="x",
            is_active=True,
        )
        db.session.add(self.admin)
        db.session.commit()
        self.cbc = TestCatalog.query.filter_by(code="CBC").first()
        if not self.cbc:
            self.cbc = TestCatalog(
                code="CBC",
                name="Complete Blood Count",
                category="Hematology",
                sample_type="Blood",
                price=100000,
            )
            db.session.add(self.cbc)
            db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _session(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.admin.id
            sess["role"] = self.admin.role
            sess["email"] = self.admin.email

    def _patient(self, label: str):
        return biz.create_patient(
            full_name=f"SMOKE {label}",
            phone=f"09{uuid.uuid4().hex[:8]}",
            patient_code=f"P-SMK-{label}-{uuid.uuid4().hex[:4].upper()}",
            actor=self.admin.email,
        )

    def test_scenario_1_home_creates_field_request_and_collector_job(self):
        """Reception → CBC → HOME + address → order + SC + field request + collector queue."""
        patient = self._patient("HOME")
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.cbc.id],
            collection_mode="HOME",
            pickup={
                "pickup_address": "12 Nguyen Trai",
                "pickup_province": "Ha Noi",
                "pickup_district": "Thanh Xuan",
                "pickup_ward": "Nhan Chinh",
                "contact_person": patient.full_name,
                "contact_phone": "0901234567",
                "requested_date": "2026-08-01",
                "requested_time_window": "08:00-10:00",
                "specimen_type": "BLOOD",
                "priority": "ROUTINE",
            },
            actor=self.admin.email,
            organization_id="org-smoke",
        )
        db.session.commit()

        # ✓ Order created
        self.assertIn("order", result)
        self.assertTrue(result["order"].get("order_code"))

        # ✓ SampleCollection created
        self.assertIn("sample_collection_id", result)
        sc = SampleCollection.query.get(result["sample_collection_id"])
        self.assertIsNotNone(sc)
        self.assertEqual(sc.collection_mode, MODE_HOME_COLLECTION)
        self.assertEqual(sc.status, ST_REQUESTED)
        self.assertEqual(sc.pickup_address, "12 Nguyen Trai")
        self.assertIsNone(sc.collector_id)

        # ✓ Field Collection Request created (REQUESTED)
        field_board = list_home_field_requests()
        self.assertIn(sc.id, {i["id"] for i in field_board["items"]})
        home_only = [i for i in field_board["items"] if i.get("collection_mode") == MODE_HOME_COLLECTION]
        self.assertIn(sc.id, {i["id"] for i in home_only})

        # ✓ Collector queue does NOT show unassigned REQUESTED jobs
        collector = list_production_queue()
        collector_ids = {i["id"] for i in collector["items"]}
        self.assertNotIn(sc.id, collector_ids)

        # API parity — field requests
        self._session()
        fq = self.client.get("/api/v1/sample-collections/queue")
        self.assertEqual(fq.status_code, 200)
        self.assertNotIn(sc.id, {i["id"] for i in fq.get_json()["data"]["items"]})
        fr = self.client.get("/api/v1/reception/workspace/field-collection-requests")
        self.assertEqual(fr.status_code, 200)
        self.assertIn(sc.id, {i["id"] for i in fr.get_json()["data"]["items"]})
        fr2 = self.client.get("/api/v1/reception/field-requests")
        self.assertEqual(fr2.status_code, 200)
        self.assertIn(sc.id, {i["id"] for i in fr2.get_json()["data"]["items"]})

    def test_scenario_2_at_reception_no_collector_queue(self):
        """Reception → CBC → AT_RECEPTION → order + SC, NO collector queue."""
        patient = self._patient("DESK")
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.cbc.id],
            collection_mode="AT_RECEPTION",
            pickup={"specimen_type": "BLOOD"},
            actor=self.admin.email,
        )
        db.session.commit()

        self.assertIn("order", result)
        self.assertTrue(result["order"].get("order_code"))
        self.assertIn("sample_collection_id", result)
        sc = SampleCollection.query.get(result["sample_collection_id"])
        self.assertIsNotNone(sc)
        self.assertEqual(sc.collection_mode, MODE_AT_RECEPTION)
        self.assertEqual(sc.status, ST_REQUESTED)
        self.assertEqual(sc.collection_location, "Reception Desk")

        desk = list_reception_desk_queue()
        self.assertIn(sc.id, {i["id"] for i in desk["items"]})

        # ✓ NO collector queue
        collector = list_production_queue()
        self.assertNotIn(sc.id, {i["id"] for i in collector["items"]})
        field = list_field_collector_queue()
        self.assertNotIn(sc.id, {i["id"] for i in field["items"]})
        home_board = list_home_field_requests()
        self.assertNotIn(sc.id, {i["id"] for i in home_board["items"]})

        self._session()
        fq = self.client.get("/api/v1/sample-collections/queue")
        self.assertEqual(fq.status_code, 200)
        self.assertNotIn(sc.id, {i["id"] for i in fq.get_json()["data"]["items"]})
        dq = self.client.get("/api/v1/reception/workspace/desk-collections")
        self.assertEqual(dq.status_code, 200)
        self.assertIn(sc.id, {i["id"] for i in dq.get_json()["data"]["items"]})

    def test_scenario_3_clinic_request_not_on_home_collector_queue(self):
        """Reception → CBC → CLINIC → order + clinic request, NO home collector queue."""
        patient = self._patient("CLINIC")
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.cbc.id],
            collection_mode="CLINIC",
            pickup={
                "clinic_name": "DxCon Partner Clinic",
                "requested_date": "2026-08-02",
                "requested_time_window": "09:00",
                "specimen_type": "BLOOD",
                "notes": "Clinic pickup",
            },
            actor=self.admin.email,
            organization_id="org-smoke",
        )
        db.session.commit()

        self.assertIn("order", result)
        self.assertTrue(result["order"].get("order_code"))
        self.assertIn("sample_collection_id", result)
        sc = SampleCollection.query.get(result["sample_collection_id"])
        self.assertIsNotNone(sc)
        self.assertEqual(sc.collection_mode, MODE_CLINIC_COLLECTION)
        self.assertEqual(sc.status, ST_REQUESTED)
        self.assertEqual(sc.clinic_name, "DxCon Partner Clinic")
        self.assertEqual(sc.collection_location, "DxCon Partner Clinic")

        # ✓ Clinic request created (field requests board includes CLINIC)
        field_board = list_home_field_requests()
        clinic_items = [i for i in field_board["items"] if i["id"] == sc.id]
        self.assertEqual(len(clinic_items), 1)
        self.assertEqual(clinic_items[0]["collection_mode"], MODE_CLINIC_COLLECTION)

        # ✓ NO Home collector queue (default collector queue is HOME-only)
        collector = list_production_queue()
        self.assertNotIn(sc.id, {i["id"] for i in collector["items"]})
        home_queue = list_field_collector_queue()
        self.assertNotIn(sc.id, {i["id"] for i in home_queue["items"]})
        desk = list_reception_desk_queue()
        self.assertNotIn(sc.id, {i["id"] for i in desk["items"]})

        self._session()
        fq = self.client.get("/api/v1/sample-collections/queue")
        self.assertEqual(fq.status_code, 200)
        self.assertNotIn(sc.id, {i["id"] for i in fq.get_json()["data"]["items"]})
        fr = self.client.get("/api/v1/reception/workspace/field-collection-requests")
        self.assertEqual(fr.status_code, 200)
        self.assertIn(sc.id, {i["id"] for i in fr.get_json()["data"]["items"]})


if __name__ == "__main__":
    unittest.main()
