"""Authoritative collection_mode routing — desk vs field queues."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_cmr_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from app import create_app
from app.business_engine import service as biz
from app.extensions.db import db
from app.models.sample_collection import SampleCollection
from app.models.test_catalog import TestCatalog
from app.models.user import User
from app.reception_workspace.service import create_reception_order, register_patient
from app.sample_collection_workspace.collection_domain import (
    MODE_AT_RECEPTION,
    MODE_CLINIC_COLLECTION,
    MODE_HOME_COLLECTION,
    ST_COLLECTED,
    ST_PENDING_ASSIGNMENT,
    ST_REQUESTED,
    ST_VERIFIED,
    CollectionDomainError,
    assert_transition,
)
from app.sample_collection_workspace.collection_routing import (
    ensure_collection_for_order,
    list_field_collector_queue,
    list_home_field_requests,
    list_reception_desk_queue,
)
from app.sample_collection_workspace.service import list_production_queue
from app.services.sample_collection_workflow import SampleCollectionWorkflowService


class CollectionModeRoutingTests(unittest.TestCase):
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
        self.blood = TestCatalog.query.filter_by(code="CBC").first() or TestCatalog.query.first()
        self.consult = TestCatalog(
            code=f"CONS-{uuid.uuid4().hex[:4].upper()}",
            name="Consult Only",
            category="Service",
            sample_type="consult",
            price=1,
        )
        db.session.add(self.consult)
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

    def _patient(self):
        return biz.create_patient(
            full_name="CMR PATIENT",
            phone=f"0911{uuid.uuid4().hex[:6]}",
            patient_code=f"P-CMR-{uuid.uuid4().hex[:6].upper()}",
            actor=self.admin.email,
        )

    def test_a_patient_registration_alone_creates_no_collection(self):
        register_patient(
            {
                "full_name": "NO ORDER",
                "phone": f"0922{uuid.uuid4().hex[:6]}",
                "patient_code": f"P-NO-{uuid.uuid4().hex[:6].upper()}",
                "force": True,
            },
            actor=self.admin.email,
            force=True,
        )
        db.session.commit()
        self.assertEqual(SampleCollection.query.count(), 0)

    def test_b_at_reception_desk_not_field_queue(self):
        patient = self._patient()
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.blood.id],
            collection_mode=MODE_AT_RECEPTION,
            actor=self.admin.email,
        )
        db.session.commit()
        sc_id = result["sample_collection_id"]
        sc = SampleCollection.query.get(sc_id)
        self.assertEqual(sc.collection_mode, MODE_AT_RECEPTION)
        self.assertEqual(sc.status, ST_REQUESTED)

        desk = list_reception_desk_queue()
        self.assertIn(sc_id, {i["id"] for i in desk["items"]})
        field = list_field_collector_queue()
        self.assertNotIn(sc_id, {i["id"] for i in field["items"]})
        default_queue = list_production_queue()
        self.assertNotIn(sc_id, {i["id"] for i in default_queue["items"]})

        barcode = result["order"].get("barcode_value") or f"BC-{result['order']['order_code']}"
        SampleCollectionWorkflowService.verify_identifiers(
            sc_id,
            patient_name=result["order"]["patient_name"],
            booking_code=result["order"]["order_code"],
            actor_email=self.admin.email,
        )
        SampleCollectionWorkflowService.record_collection_by_id(
            sc_id, scanned_barcode=barcode, require_barcode=True, actor_email=self.admin.email
        )
        arrived, _ = SampleCollectionWorkflowService.receive_by_collection_id(
            sc_id, actor_email=self.admin.email
        )
        self.assertIn(arrived.status, {"RECEIVED", "ARRIVED_AT_LAB"})

    def test_c_home_collection_field_queue_and_flow(self):
        patient = self._patient()
        pickup = {
            "pickup_address": "12 Nguyen Trai",
            "pickup_province": "Ha Noi",
            "pickup_district": "Thanh Xuan",
            "pickup_ward": "Nhan Chinh",
            "contact_person": "CMR PATIENT",
            "contact_phone": "0901234567",
            "requested_date": "2026-08-01",
            "requested_time_window": "08:00-10:00",
            "specimen_type": "BLOOD",
            "priority": "ROUTINE",
        }
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.blood.id],
            collection_mode=MODE_HOME_COLLECTION,
            pickup=pickup,
            actor=self.admin.email,
            organization_id="org-home",
        )
        db.session.commit()
        sc_id = result["sample_collection_id"]
        sc = SampleCollection.query.get(sc_id)
        self.assertEqual(sc.collection_mode, MODE_HOME_COLLECTION)
        self.assertEqual(sc.status, ST_PENDING_ASSIGNMENT)
        self.assertEqual(sc.pickup_address, "12 Nguyen Trai")
        self.assertIsNotNone(sc.sample_tracking_id)
        self.assertIsNone(sc.collector_id)
        home_board = list_home_field_requests()
        self.assertIn(sc_id, {i["id"] for i in home_board["items"]})

        self.assertIn(sc_id, {i["id"] for i in list_field_collector_queue()["items"]})
        self.assertNotIn(sc_id, {i["id"] for i in list_reception_desk_queue()["items"]})

        # Dispatcher assignment before collector workflow
        sc.collector_name = "Field Collector"
        sc.collector_id = "collector-1"
        sc.status = "ASSIGNED"
        db.session.commit()

        barcode = result["order"].get("barcode_value") or f"BC-{result['order']['order_code']}"
        SampleCollectionWorkflowService.verify_identifiers(
            sc_id,
            patient_name=result["order"]["patient_name"],
            booking_code=result["order"]["order_code"],
            actor_email=self.admin.email,
        )
        SampleCollectionWorkflowService.record_collection_by_id(
            sc_id, scanned_barcode=barcode, require_barcode=True, actor_email=self.admin.email
        )
        SampleCollectionWorkflowService.dispatch_by_collection_id(sc_id, actor_email=self.admin.email)
        SampleCollectionWorkflowService.receive_by_collection_id(sc_id, actor_email=self.admin.email)
        self.assertEqual(SampleCollection.query.get(sc_id).status in {"RECEIVED", "ARRIVED_AT_LAB"}, True)

    def test_d_clinic_collection(self):
        patient = self._patient()
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.blood.id],
            collection_mode=MODE_CLINIC_COLLECTION,
            pickup={
                "clinic_name": "Clinic A",
                "requested_date": "2026-08-02",
                "requested_time_window": "14:00-16:00",
                "specimen_type": "BLOOD",
            },
            actor=self.admin.email,
        )
        db.session.commit()
        sc = SampleCollection.query.get(result["sample_collection_id"])
        self.assertEqual(sc.collection_mode, MODE_CLINIC_COLLECTION)
        # Clinic request exists on field-request board, not home collector queue
        self.assertIn(sc.id, {i["id"] for i in list_home_field_requests()["items"]})
        self.assertNotIn(sc.id, {i["id"] for i in list_field_collector_queue()["items"]})
        self.assertNotIn(sc.id, {i["id"] for i in list_production_queue()["items"]})
        self.assertNotIn(sc.id, {i["id"] for i in list_reception_desk_queue()["items"]})

    def test_e_non_specimen_no_collection(self):
        patient = self._patient()
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.consult.id],
            collection_mode=MODE_AT_RECEPTION,
            actor=self.admin.email,
        )
        db.session.commit()
        self.assertNotIn("sample_collection_id", result)
        self.assertEqual(SampleCollection.query.count(), 0)

    def test_f_idempotent_retries(self):
        patient = self._patient()
        first = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.blood.id],
            collection_mode=MODE_AT_RECEPTION,
            actor=self.admin.email,
        )
        db.session.commit()
        from app.models.biz_order import BizOrder

        order = BizOrder.query.get(first["order"]["id"])
        second = ensure_collection_for_order(order, collection_mode=MODE_AT_RECEPTION)
        third = ensure_collection_for_order(order, collection_mode=MODE_AT_RECEPTION)
        self.assertEqual(first["sample_collection_id"], second.id)
        self.assertEqual(second.id, third.id)
        self.assertEqual(SampleCollection.query.filter_by(order_id=order.id).count(), 1)

    def test_g_invalid_transition_409(self):
        with self.assertRaises(CollectionDomainError) as ctx:
            assert_transition(ST_REQUESTED, ST_COLLECTED)
        self.assertEqual(ctx.exception.status_code, 409)

    def test_h_organization_isolation_field(self):
        a = create_reception_order(
            patient_code=self._patient().patient_code,
            test_catalog_ids=[self.blood.id],
            collection_mode=MODE_HOME_COLLECTION,
            pickup={
                "pickup_address": "A",
                "pickup_province": "HN",
                "pickup_district": "D1",
                "contact_person": "A",
                "contact_phone": "1",
                "requested_date": "2026-08-01",
                "requested_time_window": "am",
            },
            organization_id="org-A",
            actor=self.admin.email,
        )
        b = create_reception_order(
            patient_code=self._patient().patient_code,
            test_catalog_ids=[self.blood.id],
            collection_mode=MODE_HOME_COLLECTION,
            pickup={
                "pickup_address": "B",
                "pickup_province": "HCM",
                "pickup_district": "D2",
                "contact_person": "B",
                "contact_phone": "2",
                "requested_date": "2026-08-01",
                "requested_time_window": "pm",
            },
            organization_id="org-B",
            actor=self.admin.email,
        )
        db.session.commit()
        scoped = list_field_collector_queue(role="COLLECTOR", organization_id="org-A")
        ids = {i["id"] for i in scoped["items"]}
        self.assertIn(a["sample_collection_id"], ids)
        self.assertNotIn(b["sample_collection_id"], ids)

    def test_i_home_missing_pickup_rejected(self):
        patient = self._patient()
        with self.assertRaises(Exception):
            create_reception_order(
                patient_code=patient.patient_code,
                test_catalog_ids=[self.blood.id],
                collection_mode=MODE_HOME_COLLECTION,
                pickup={},
                actor=self.admin.email,
            )

    def test_api_desk_and_field_endpoints(self):
        patient = self._patient()
        desk = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.blood.id],
            collection_mode=MODE_AT_RECEPTION,
            actor=self.admin.email,
        )
        field = create_reception_order(
            patient_code=self._patient().patient_code,
            test_catalog_ids=[self.blood.id],
            collection_mode=MODE_HOME_COLLECTION,
            pickup={
                "pickup_address": "Addr",
                "pickup_province": "City",
                "pickup_district": "D",
                "contact_person": "Contact",
                "contact_phone": "090",
                "requested_date": "2026-08-01",
                "requested_time_window": "am",
            },
            actor=self.admin.email,
        )
        db.session.commit()
        self._session()
        dq = self.client.get("/api/v1/reception/workspace/desk-collections")
        self.assertEqual(dq.status_code, 200)
        desk_ids = {i["id"] for i in dq.get_json()["data"]["items"]}
        self.assertIn(desk["sample_collection_id"], desk_ids)
        self.assertNotIn(field["sample_collection_id"], desk_ids)

        fq = self.client.get("/api/v1/sample-collections/queue")
        self.assertEqual(fq.status_code, 200)
        field_ids = {i["id"] for i in fq.get_json()["data"]["items"]}
        self.assertIn(field["sample_collection_id"], field_ids)
        self.assertNotIn(desk["sample_collection_id"], field_ids)



    def test_j_blank_sample_type_still_creates_collection(self):
        blank_catalog = TestCatalog(
            code=f"BLNK-{uuid.uuid4().hex[:4].upper()}",
            name="Blank Sample Type",
            category="Lab",
            sample_type=None,
            price=1,
        )
        db.session.add(blank_catalog)
        db.session.commit()
        patient = self._patient()
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[blank_catalog.id],
            collection_mode=MODE_AT_RECEPTION,
            actor=self.admin.email,
        )
        db.session.commit()
        self.assertIn("sample_collection_id", result)
        sc = SampleCollection.query.get(result["sample_collection_id"])
        self.assertIsNotNone(sc)
        self.assertEqual(sc.collection_mode, MODE_AT_RECEPTION)

    def test_k_compatible_enrich_keeps_home_in_collector_queue(self):
        patient = self._patient()
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.blood.id],
            collection_mode=MODE_HOME_COLLECTION,
            pickup={
                "pickup_address": "99 Compatible Lane",
                "pickup_province": "HN",
                "pickup_district": "D1",
                "contact_person": "CMR PATIENT",
                "contact_phone": "0901111222",
                "requested_date": "2026-08-03",
                "requested_time_window": "10:00-12:00",
                "specimen_type": "BLOOD",
            },
            actor=self.admin.email,
        )
        db.session.commit()
        sc_id = result["sample_collection_id"]
        sc = SampleCollection.query.get(sc_id)
        self.assertEqual(sc.collection_mode, MODE_HOME_COLLECTION)

        live_columns = set(SampleCollectionWorkflowService._sample_collection_db_columns())
        live_columns.discard("collection_mode")

        with patch.object(
            SampleCollectionWorkflowService,
            "_sample_collection_db_columns",
            return_value=live_columns,
        ):
            payload = SampleCollectionWorkflowService._enrich_payload(sc, live_columns)
            self.assertEqual(payload.get("collection_mode"), MODE_HOME_COLLECTION)
            queue = list_field_collector_queue()
        self.assertIn(sc_id, {i["id"] for i in queue["items"]})

    def test_l_null_partner_id_visible_to_org_collector(self):
        patient = self._patient()
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.blood.id],
            collection_mode=MODE_HOME_COLLECTION,
            pickup={
                "pickup_address": "Unassigned Org Row",
                "pickup_province": "HN",
                "pickup_district": "D1",
                "contact_person": "CMR PATIENT",
                "contact_phone": "0903333444",
                "requested_date": "2026-08-04",
                "requested_time_window": "08:00-10:00",
                "specimen_type": "BLOOD",
            },
            actor=self.admin.email,
        )
        db.session.commit()
        sc = SampleCollection.query.get(result["sample_collection_id"])
        sc.partner_id = None
        db.session.commit()

        scoped = list_field_collector_queue(role="COLLECTOR", organization_id="org-home")
        self.assertIn(sc.id, {i["id"] for i in scoped["items"]})
        board = list_home_field_requests(role="COLLECTOR", organization_id="org-home")
        self.assertIn(sc.id, {i["id"] for i in board["items"]})

if __name__ == "__main__":
    unittest.main()
