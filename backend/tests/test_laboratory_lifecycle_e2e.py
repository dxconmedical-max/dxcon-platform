"""E2E smoke: Reception → Collector → Lab Arrival sync → Lab → Released Result."""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_lifecycle_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from app import create_app
from app.business_engine import service as biz
from app.business_engine.statuses import ORDER_APPROVED, ORDER_LAB_RECEIVED, ORDER_RELEASED
from app.extensions.db import db
from app.lab_workspace.service import (
    assign_processing,
    create_accession,
    enter_result_manual,
    mark_qc_passed,
    medical_reject,
    medical_reopen,
    medical_validate,
    receive_sample,
    release_result,
    start_processing,
    validate_result,
)
from app.models.audit_log import AuditLog
from app.models.biz_order import BizLabQueueItem, BizOrder
from app.models.sample_collection import SampleCollection
from app.models.test_catalog import TestCatalog
from app.models.user import User
from app.reception_workspace.service import create_reception_order
from app.sample_collection_workspace.collection_domain import (
    MODE_AT_RECEPTION,
    MODE_HOME_COLLECTION,
    ST_ASSIGNED,
    ST_PENDING_ASSIGNMENT,
)
from app.sample_collection_workspace.collection_routing import (
    assign_collector,
    list_field_collector_queue,
    list_home_field_requests,
    release_collector_assignment,
)
from app.sample_collection_workspace.service import list_production_queue
from app.services.sample_collection_workflow import SampleCollectionWorkflowService


class LaboratoryLifecycleE2ETests(unittest.TestCase):
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
        self.cbc = TestCatalog.query.filter_by(code="CBC").first() or TestCatalog.query.first()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _patient(self, label: str):
        return biz.create_patient(
            full_name=f"LC {label}",
            phone=f"09{uuid.uuid4().hex[:8]}",
            patient_code=f"P-LC-{label}-{uuid.uuid4().hex[:4].upper()}",
            actor=self.admin.email,
        )

    def test_p0_lab_arrival_syncs_order_and_lab_queue(self):
        patient = self._patient("ARR")
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.cbc.id],
            collection_mode=MODE_AT_RECEPTION,
            pickup={"specimen_type": "BLOOD"},
            actor=self.admin.email,
        )
        db.session.commit()
        sc_id = result["sample_collection_id"]
        order_code = result["order"]["order_code"]
        barcode = result["order"].get("barcode_value") or f"BC-{order_code}"

        SampleCollectionWorkflowService.verify_identifiers(
            sc_id,
            patient_name=result["order"]["patient_name"],
            booking_code=order_code,
            actor_email=self.admin.email,
        )
        SampleCollectionWorkflowService.record_collection_by_id(
            sc_id, scanned_barcode=barcode, require_barcode=True, actor_email=self.admin.email
        )
        collection, sample = SampleCollectionWorkflowService.receive_by_collection_id(
            sc_id, actor_email=self.admin.email
        )
        self.assertEqual(collection.status, "ARRIVED_AT_LAB")
        self.assertIsNotNone(collection.arrived_at_lab)
        self.assertEqual(sample.status, "RECEIVED")

        order = BizOrder.query.filter_by(order_code=order_code).first()
        self.assertEqual(order.status, ORDER_LAB_RECEIVED)
        lab_item = BizLabQueueItem.query.filter_by(order_id=order.id).first()
        self.assertIsNotNone(lab_item)

        audits = AuditLog.query.filter_by(object_type="SampleCollection", object_id=sc_id).all()
        self.assertTrue(any(a.action == "SAMPLE_COLLECTION_LAB_RECEIVED" for a in audits))

    def test_p1_collector_assign_reassign_release(self):
        patient = self._patient("ASN")
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.cbc.id],
            collection_mode=MODE_HOME_COLLECTION,
            pickup={
                "pickup_address": "1 Test St",
                "pickup_province": "HN",
                "pickup_district": "D",
                "contact_person": "A",
                "contact_phone": "090",
                "requested_date": "2026-08-01",
                "requested_time_window": "am",
                "specimen_type": "BLOOD",
            },
            actor=self.admin.email,
            organization_id="org-1",
        )
        db.session.commit()
        sc_id = result["sample_collection_id"]
        sc = SampleCollection.query.get(sc_id)
        self.assertEqual(sc.status, ST_PENDING_ASSIGNMENT)

        assigned = assign_collector(
            sc_id,
            collector_id=self.collector.id,
            collector_name="Field Col",
            actor=self.admin.email,
        )
        db.session.commit()
        self.assertEqual(assigned.status, ST_ASSIGNED)
        self.assertEqual(assigned.collector_id, self.collector.id)
        self.assertIn(sc_id, {i["id"] for i in list_production_queue()["items"]})

        other = User(
            email=f"col2-{uuid.uuid4().hex[:4]}@test.local",
            role="COLLECTOR",
            password_hash="x",
            is_active=True,
        )
        db.session.add(other)
        db.session.commit()
        reassigned = assign_collector(sc_id, collector_id=other.id, actor=self.admin.email)
        db.session.commit()
        self.assertEqual(reassigned.collector_id, other.id)

        released = release_collector_assignment(sc_id, actor=self.admin.email)
        db.session.commit()
        self.assertEqual(released.status, ST_PENDING_ASSIGNMENT)
        self.assertIsNone(released.collector_id)
        self.assertIn(sc_id, {i["id"] for i in list_home_field_requests()["items"]})

    def test_p1_medical_reject_reopen_and_release(self):
        # Seed via biz path to lab_received then full lab chain
        catalog = self.cbc
        patient = self._patient("MED")
        order = biz.create_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[catalog.id],
            actor=self.admin.email,
        )
        biz.mark_order_paid(order.order_code, payment_method="cash", actor=self.admin.email)
        biz.create_collection_job(order.order_code, collector_name="C", pickup_address="Desk", actor="t")
        biz.accept_collection(order.order_code, actor="t")
        biz.collect_sample(order.order_code, actor="t")
        biz.handover_sample(order.order_code, actor="t")
        receive_sample(order_code=order.order_code, received_by="Lab", actor="lab")
        create_accession(order_code=order.order_code, accessioned_by="Lab", actor="lab")
        assign_processing(order_code=order.order_code, bench_id="B1", instrument_id="I1", technician="t", actor="lab")
        start_processing(order_code=order.order_code, actor="lab")
        enter_result_manual(
            order.order_code,
            test_code=catalog.code,
            result_value="4.2",
            unit="g/dL",
            reference_range="3.5-5.5",
            actor="lab",
        )
        mark_qc_passed(order.order_code, actor="lab")
        validate_result(order.order_code, actor="lab")
        db.session.commit()

        medical_validate(order.order_code, doctor_note="ok", actor=self.admin.email)
        db.session.commit()
        self.assertEqual(BizOrder.query.filter_by(order_code=order.order_code).first().status, ORDER_APPROVED)

        medical_reopen(order.order_code, reason="need check", actor=self.admin.email)
        db.session.commit()
        self.assertEqual(BizOrder.query.filter_by(order_code=order.order_code).first().status, "pending_review")

        medical_reject(order.order_code, reason="fix result", actor=self.admin.email)
        db.session.commit()
        self.assertEqual(BizOrder.query.filter_by(order_code=order.order_code).first().status, "testing")

        # Re-tech + medical + release
        mark_qc_passed(order.order_code, actor="lab")
        validate_result(order.order_code, actor="lab")
        medical_validate(order.order_code, doctor_note="final", actor=self.admin.email)
        released = release_result(order.order_code, actor=self.admin.email)
        db.session.commit()
        self.assertEqual(released["status"], ORDER_RELEASED)
        self.assertTrue(released["email_ready"])
        self.assertTrue(released["html_ready"])
        order = BizOrder.query.filter_by(order_code=order.order_code).first()
        self.assertEqual(order.status, ORDER_RELEASED)

        audits = AuditLog.query.filter(
            AuditLog.action.in_(
                [
                    "lab.medical_validation",
                    "lab.medical_validation_reopened",
                    "lab.medical_validation_rejected",
                    "lab.result_released",
                    "lab.result_email_ready",
                ]
            )
        ).all()
        actions = {a.action for a in audits}
        self.assertIn("lab.result_released", actions)
        self.assertIn("lab.medical_validation_reopened", actions)

    def test_p2_full_reception_to_released_smoke(self):
        patient = self._patient("E2E")
        created = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.cbc.id],
            collection_mode="HOME",
            pickup={
                "pickup_address": "99 Smoke Rd",
                "pickup_province": "HCM",
                "pickup_district": "Q1",
                "contact_person": patient.full_name,
                "contact_phone": "0912345678",
                "requested_date": "2026-08-10",
                "requested_time_window": "09:00-11:00",
                "specimen_type": "BLOOD",
                "priority": "ROUTINE",
            },
            actor=self.admin.email,
            organization_id="org-e2e",
        )
        db.session.commit()
        sc_id = created["sample_collection_id"]
        order_code = created["order"]["order_code"]
        barcode = created["order"].get("barcode_value") or f"BC-{order_code}"

        assign_collector(sc_id, collector_id=self.collector.id, collector_name="E2E Collector", actor=self.admin.email)
        db.session.commit()
        self.assertIn(sc_id, {i["id"] for i in list_field_collector_queue()["items"]})

        SampleCollectionWorkflowService.verify_identifiers(
            sc_id,
            patient_name=created["order"]["patient_name"],
            booking_code=order_code,
            actor_email=self.collector.email,
        )
        SampleCollectionWorkflowService.record_collection_by_id(
            sc_id, scanned_barcode=barcode, require_barcode=True, actor_email=self.collector.email
        )
        SampleCollectionWorkflowService.dispatch_by_collection_id(sc_id, actor_email=self.collector.email)
        SampleCollectionWorkflowService.receive_by_collection_id(sc_id, actor_email=self.admin.email)

        order = BizOrder.query.filter_by(order_code=order_code).first()
        self.assertEqual(order.status, ORDER_LAB_RECEIVED)
        self.assertIsNotNone(BizLabQueueItem.query.filter_by(order_id=order.id).first())

        create_accession(order_code=order_code, accessioned_by="Lab", actor="lab")
        assign_processing(
            order_code=order_code, bench_id="B1", instrument_id="I1", technician="tech", actor="lab"
        )
        start_processing(order_code=order_code, actor="lab")
        enter_result_manual(
            order_code,
            test_code=self.cbc.code,
            result_value="5.0",
            unit="g/dL",
            reference_range="3.5-5.5",
            actor="lab",
        )
        mark_qc_passed(order_code, actor="lab")
        validate_result(order_code, actor="lab")
        medical_validate(order_code, doctor_note="cleared", actor=self.admin.email)
        released = release_result(order_code, actor=self.admin.email)
        db.session.commit()

        self.assertEqual(released["status"], ORDER_RELEASED)
        self.assertTrue(released.get("html_content") or released.get("html_ready"))
        sc = SampleCollection.query.get(sc_id)
        self.assertEqual(sc.status, "RELEASED")
        self.assertEqual(BizOrder.query.filter_by(order_code=order_code).first().status, ORDER_RELEASED)


if __name__ == "__main__":
    unittest.main()
