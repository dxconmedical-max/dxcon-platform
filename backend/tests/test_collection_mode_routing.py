"""Authoritative collection_mode routing — desk vs field queues."""

from __future__ import annotations

import os
import tempfile
import unittest
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
    ST_REQUESTED,
    ST_VERIFIED,
    CollectionDomainError,
    assert_transition,
)
from app.sample_collection_workspace.collection_routing import (
    ensure_collection_for_order,
    list_field_collector_queue,
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
            "pickup_city": "Ha Noi",
            "contact_phone": "0901234567",
            "requested_date": "2026-08-01",
            "requested_time_window": "08:00-10:00",
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
        self.assertEqual(sc.pickup_address, "12 Nguyen Trai")

        self.assertIn(sc_id, {i["id"] for i in list_field_collector_queue()["items"]})
        self.assertNotIn(sc_id, {i["id"] for i in list_reception_desk_queue()["items"]})

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
                "pickup_address": "Clinic A",
                "pickup_city": "Da Nang",
                "contact_phone": "0909999999",
                "requested_date": "2026-08-02",
                "requested_time_window": "14:00-16:00",
            },
            actor=self.admin.email,
        )
        db.session.commit()
        sc = SampleCollection.query.get(result["sample_collection_id"])
        self.assertEqual(sc.collection_mode, MODE_CLINIC_COLLECTION)
        self.assertIn(sc.id, {i["id"] for i in list_field_collector_queue()["items"]})

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
                "pickup_city": "HN",
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
                "pickup_city": "HCM",
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
                "pickup_city": "City",
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


if __name__ == "__main__":
    unittest.main()
