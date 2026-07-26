"""Laboratory Workflow — receipt through medical validation."""

from __future__ import annotations

import os
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.business_engine import service as biz
from app.business_engine.statuses import (
    ORDER_APPROVED,
    ORDER_LAB_RECEIVED,
    ORDER_PENDING_REVIEW,
    ORDER_TESTING,
)
from app.extensions.db import db
from app.lab_workspace.flags import calculate_abnormal_flag
from app.lab_workspace.service import (
    LabWorkspaceError,
    assign_processing,
    create_accession,
    enter_result_manual,
    get_order_workspace,
    ingest_analyzer_result,
    mark_qc_passed,
    medical_validate,
    next_accession_number,
    receive_sample,
    reject_result,
    start_processing,
    status_contract,
    validate_result,
    verify_identifiers,
)
from app.models.audit_log import AuditLog
from app.models.biz_order import BizCollection, BizOrder, BizResult
from app.models.lab_lis import LabAccessionRecord
from app.models.user import User


def _seed_to_transit(tag: str):
    biz.ensure_test_catalog_seed()
    catalog = biz.ensure_test_catalog_seed()[0]
    patient = biz.create_patient(
        full_name=f"Lab WF {tag}",
        phone=f"09{tag[:8].ljust(8, '0')}",
        actor="test@dxcon.test",
    )
    order = biz.create_order(
        patient_code=patient.patient_code,
        test_catalog_ids=[catalog.id],
        actor="test@dxcon.test",
    )
    biz.mark_order_paid(order.order_code, payment_method="cash", actor="test@dxcon.test")
    biz.create_collection_job(order.order_code, collector_name="C", pickup_address="Desk", actor="test")
    biz.accept_collection(order.order_code, actor="test")
    biz.collect_sample(order.order_code, actor="test")
    biz.handover_sample(order.order_code, actor="test")
    db.session.commit()
    return order, catalog


class LaboratoryWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.tag = uuid.uuid4().hex[:6].upper()
        self.lab_user = User(
            email=f"lab-{self.tag}@test.local",
            role="LAB",
            password_hash="x",
            is_active=True,
        )
        self.doctor = User(
            email=f"doc-{self.tag}@test.local",
            role="DOCTOR",
            password_hash="x",
            is_active=True,
        )
        self.collector = User(
            email=f"col-{self.tag}@test.local",
            role="COLLECTOR",
            password_hash="x",
            is_active=True,
        )
        db.session.add_all([self.lab_user, self.doctor, self.collector])
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        try:
            db.drop_all()
        except Exception:
            pass
        self.ctx.pop()

    def _session(self, user: User):
        with self.client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["email"] = user.email

    def test_status_contract_and_accession_format(self):
        contract = status_contract()
        self.assertIn("lab_received", contract["order_flow"])
        self.assertEqual(contract["accession_id_format"], "ACC-YYYYMMDD-000001")
        acc = next_accession_number()
        self.assertTrue(acc.startswith("ACC-"))
        self.assertEqual(len(acc.split("-")[-1]), 6)

    def test_receipt_and_refresh_persistence(self):
        order, _ = _seed_to_transit(self.tag)
        collection = BizCollection.query.filter_by(order_id=order.id).first()
        recv = receive_sample(
            order_code=order.order_code,
            sample_code=collection.sample_code,
            received_by="Lab Tech",
            condition_status="acceptable",
            actor="lab@test",
        )
        db.session.commit()
        self.assertEqual(recv["status"], ORDER_LAB_RECEIVED)
        refreshed = BizOrder.query.filter_by(order_code=order.order_code).first()
        self.assertEqual(refreshed.status, ORDER_LAB_RECEIVED)
        again = receive_sample(
            order_code=order.order_code,
            received_by="Lab Tech",
            condition_status="acceptable",
            actor="lab@test",
        )
        self.assertTrue(again.get("idempotent"))

    def test_rejection_structured_reason(self):
        order, _ = _seed_to_transit(self.tag + "R")
        out = receive_sample(
            order_code=order.order_code,
            received_by="Lab Tech",
            condition_status="rejected",
            rejection_reason="hemolyzed",
            note="gross hemolysis",
            actor="lab@test",
        )
        db.session.commit()
        self.assertEqual(out["status"], "rejected")
        self.assertEqual(out["rejection_reason"], "hemolyzed")
        coll = BizCollection.query.filter_by(order_id=order.id).first()
        self.assertEqual(coll.condition_status, "rejected")
        with self.assertRaises(LabWorkspaceError):
            create_accession(order_code=order.order_code, accessioned_by="Lab", actor="lab@test")

    def test_identifier_verification(self):
        order, _ = _seed_to_transit(self.tag + "V")
        collection = BizCollection.query.filter_by(order_id=order.id).first()
        ok = verify_identifiers(
            order_code=order.order_code,
            sample_code=collection.sample_code,
            patient_code=order.patient_code,
            actor="lab@test",
        )
        self.assertTrue(ok["ok"])
        bad = verify_identifiers(
            order_code=order.order_code,
            patient_code="WRONG",
            actor="lab@test",
        )
        self.assertFalse(bad["ok"])
        self.assertIn("patient_code", bad["mismatches"])

    def test_accession_processing_result_critical_tech_medical(self):
        order, catalog = _seed_to_transit(self.tag + "E")
        receive_sample(order_code=order.order_code, received_by="Lab", actor="lab@test")
        db.session.commit()
        acc = create_accession(order_code=order.order_code, accessioned_by="Lab", actor="lab@test")
        db.session.commit()
        self.assertTrue(acc["accession_number"].startswith("ACC-"))
        self.assertEqual(acc["processing_status"], "accessioned")

        assigned = assign_processing(
            order_code=order.order_code,
            bench_id="B1",
            instrument_id="I1",
            technician="tech.a",
            actor="lab@test",
        )
        self.assertEqual(assigned["processing_status"], "assigned")
        started = start_processing(order_code=order.order_code, actor="lab@test")
        self.assertEqual(started["processing_status"], "processing")
        self.assertIsNotNone(started["processing_started_at"])
        db.session.commit()

        with self.assertRaises(LabWorkspaceError):
            enter_result_manual(
                order.order_code,
                test_code=catalog.code,
                result_value="",
                actor="lab@test",
            )

        critical = enter_result_manual(
            order.order_code,
            test_code=catalog.code,
            result_value="9.5",
            unit="mmol/L",
            reference_range="3.5-5.5",
            critical_low=2.0,
            critical_high=8.0,
            actor="lab@test",
        )
        db.session.commit()
        self.assertTrue(critical["critical"])
        self.assertEqual(critical["flag"], "critical_high")
        order = BizOrder.query.filter_by(order_code=order.order_code).first()
        self.assertEqual(order.status, ORDER_TESTING)

        mark_qc_passed(order.order_code, actor="lab@test")
        db.session.commit()
        tech = validate_result(order.order_code, actor="lab@test")
        db.session.commit()
        self.assertEqual(tech["status"], "pending_review")
        self.assertTrue(tech["locked"])
        order = BizOrder.query.filter_by(order_code=order.order_code).first()
        self.assertEqual(order.status, ORDER_PENDING_REVIEW)

        with self.assertRaises(LabWorkspaceError):
            enter_result_manual(
                order.order_code,
                test_code=catalog.code,
                result_value="4.0",
                revision_mode=True,
                actor="lab@test",
            )

        med = medical_validate(order.order_code, doctor_note="OK", actor="doc@test")
        db.session.commit()
        self.assertEqual(med["status"], ORDER_APPROVED)
        self.assertTrue(med["locked"])
        order = BizOrder.query.filter_by(order_code=order.order_code).first()
        self.assertEqual(order.status, ORDER_APPROVED)
        accession = LabAccessionRecord.query.filter_by(order_code=order.order_code).first()
        self.assertEqual(accession.processing_status, "medically_validated")

        with self.assertRaises(LabWorkspaceError):
            enter_result_manual(
                order.order_code,
                test_code=catalog.code,
                result_value="4.1",
                revision_mode=True,
                actor="lab@test",
            )

        ws = get_order_workspace(order.order_code)
        self.assertTrue(ws["locked"])

    def test_analyzer_ingest_requires_validation(self):
        order, catalog = _seed_to_transit(self.tag + "A")
        receive_sample(order_code=order.order_code, received_by="Lab", actor="lab@test")
        create_accession(order_code=order.order_code, accessioned_by="Lab", actor="lab@test")
        db.session.commit()
        data = ingest_analyzer_result(
            order.order_code,
            test_code=catalog.code,
            result_value="4.2",
            unit="g/dL",
            reference_range="3.5-5.5",
            instrument="AUTO-1",
            actor="analyzer@test",
        )
        db.session.commit()
        self.assertTrue(data["requires_validation"])
        result = BizResult.query.filter_by(order_id=order.id).first()
        self.assertEqual(result.result_source, "analyzer")
        self.assertNotEqual(result.status, "released")

    def test_tech_reject_reopens_for_edit(self):
        order, catalog = _seed_to_transit(self.tag + "T")
        receive_sample(order_code=order.order_code, received_by="Lab", actor="lab@test")
        create_accession(order_code=order.order_code, accessioned_by="Lab", actor="lab@test")
        enter_result_manual(
            order.order_code,
            test_code=catalog.code,
            result_value="4.0",
            reference_range="3.5-5.5",
            actor="lab@test",
        )
        validate_result(order.order_code, actor="lab@test")
        db.session.commit()
        reject_result(order.order_code, reason="delta check", actor="lab@test")
        db.session.commit()
        enter_result_manual(
            order.order_code,
            test_code=catalog.code,
            result_value="4.1",
            reference_range="3.5-5.5",
            revision_mode=True,
            actor="lab@test",
        )
        db.session.commit()
        result = BizResult.query.filter_by(order_id=order.id).first()
        self.assertEqual(result.workflow_status, "entered")

    def test_abnormal_flag_engine(self):
        flag, _ = calculate_abnormal_flag("1.0", reference_range="3-7", critical_low=2.0, critical_high=10.0)
        self.assertEqual(flag, "critical_low")
        flag2, _ = calculate_abnormal_flag("6", reference_range="3-7")
        self.assertEqual(flag2, "normal")

    def test_audit_trail(self):
        order, catalog = _seed_to_transit(self.tag + "U")
        receive_sample(order_code=order.order_code, received_by="Lab", actor="lab@test")
        create_accession(order_code=order.order_code, accessioned_by="Lab", actor="lab@test")
        enter_result_manual(
            order.order_code,
            test_code=catalog.code,
            result_value="4.0",
            reference_range="3-5",
            actor="lab@test",
        )
        validate_result(order.order_code, actor="lab@test")
        medical_validate(order.order_code, actor="doc@test")
        db.session.commit()
        count = AuditLog.query.filter(AuditLog.action.like("lab.%")).count()
        self.assertGreaterEqual(count, 3)

    def test_authorization_api(self):
        order, catalog = _seed_to_transit(self.tag + "Z")
        receive_sample(order_code=order.order_code, received_by="Lab", actor="lab@test")
        create_accession(order_code=order.order_code, accessioned_by="Lab", actor="lab@test")
        enter_result_manual(
            order.order_code,
            test_code=catalog.code,
            result_value="4.0",
            reference_range="3-5",
            actor="lab@test",
        )
        validate_result(order.order_code, actor="lab@test")
        db.session.commit()

        # Collector cannot medical validate
        self._session(self.collector)
        resp = self.client.post(
            "/api/v1/lab/workspace/medical-validation/approve",
            json={"order_code": order.order_code},
        )
        self.assertIn(resp.status_code, (401, 403))

        # Lab can tech-validate endpoint (already done) but medical requires doctor
        self._session(self.lab_user)
        resp = self.client.post(
            "/api/v1/lab/workspace/medical-validation/approve",
            json={"order_code": order.order_code},
        )
        self.assertIn(resp.status_code, (401, 403))

        self._session(self.doctor)
        resp = self.client.post(
            "/api/v1/lab/workspace/medical-validation/approve",
            json={"order_code": order.order_code, "doctor_note": "signed"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()["success"])

        # Lab can read dashboard
        self._session(self.lab_user)
        resp = self.client.get("/api/v1/lab/workspace/dashboard")
        self.assertEqual(resp.status_code, 200)

        # Collector cannot write receive
        self._session(self.collector)
        resp = self.client.post(
            "/api/v1/lab/workspace/receive",
            json={"order_code": order.order_code, "received_by": "x"},
        )
        self.assertIn(resp.status_code, (401, 403))

    def test_e2e_api_path(self):
        order, catalog = _seed_to_transit(self.tag + "X")
        self._session(self.lab_user)
        r = self.client.post(
            "/api/v1/lab/workspace/receive",
            json={"order_code": order.order_code, "condition_status": "acceptable", "received_by": "API"},
        )
        self.assertEqual(r.status_code, 200)
        r = self.client.post(
            "/api/v1/lab/workspace/accession",
            json={"order_code": order.order_code},
        )
        self.assertEqual(r.status_code, 201)
        acc = r.get_json()["data"]["accession_number"]
        self.assertTrue(acc.startswith("ACC-"))
        r = self.client.post(
            "/api/v1/lab/workspace/assign",
            json={"order_code": order.order_code, "bench_id": "B", "instrument_id": "I"},
        )
        self.assertEqual(r.status_code, 200)
        r = self.client.post(
            "/api/v1/lab/workspace/processing/start",
            json={"order_code": order.order_code},
        )
        self.assertEqual(r.status_code, 200)
        r = self.client.post(
            "/api/v1/lab/workspace/results",
            json={
                "order_code": order.order_code,
                "test_code": catalog.code,
                "result_value": "4.4",
                "unit": "u",
                "reference_range": "3-5",
            },
        )
        self.assertEqual(r.status_code, 201)
        r = self.client.post(
            "/api/v1/lab/workspace/validation/approve",
            json={"order_code": order.order_code},
        )
        self.assertEqual(r.status_code, 200)
        self._session(self.doctor)
        r = self.client.post(
            "/api/v1/lab/workspace/medical-validation/approve",
            json={"order_code": order.order_code},
        )
        self.assertEqual(r.status_code, 200)
        # refresh persistence
        self._session(self.lab_user)
        r = self.client.get(f"/api/v1/lab/workspace/orders/{order.order_code}")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()["data"]
        self.assertTrue(body["locked"])
        self.assertEqual(body["order"]["status"], ORDER_APPROVED)


if __name__ == "__main__":
    unittest.main()
