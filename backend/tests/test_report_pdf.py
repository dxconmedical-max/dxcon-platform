"""Production Report PDF — finalized clinical PDF generation and access control."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.business_engine import service as biz
from app.extensions.db import db
from app.lab_workspace.service import (
    create_accession,
    enter_result_manual,
    mark_qc_passed,
    receive_sample,
    validate_result,
)
from app.models.biz_order import BizCollection
from app.models.clinical_report import ClinicalReport
from app.models.user import User
from app.reporting_engine.pdf_service import (
    REPORT_PDF_TEMPLATE_ID,
    REPORT_PDF_TEMPLATE_VERSION,
    ReportPdfError,
    build_frozen_pdf_document,
    write_report_pdf,
)
from app.reporting_engine.service import (
    ReportingEngineError,
    acknowledge_critical,
    approve_report,
    create_report_amendment,
    ensure_clinical_report,
    get_report_pdf,
    release_report,
    start_review,
    verify_clinical_report,
)


def _seed_pending_review(tag: str, *, flag: str = "NORMAL", value: str = "4.2", many: int = 1):
    from app.models.biz_order import BizResult, BizResultItem

    biz.ensure_test_catalog_seed()
    catalog = biz.ensure_test_catalog_seed()
    patient = biz.create_patient(
        full_name=f"PDF Benh nhan {tag}",
        phone=f"09{tag[:8].ljust(8, '0')}",
        actor="test@dxcon.test",
    )
    order = biz.create_order(
        patient_code=patient.patient_code,
        test_catalog_ids=[catalog[0].id],
        actor="test",
    )
    biz.mark_order_paid(order.order_code, payment_method="cash", actor="test")
    biz.create_collection_job(order.order_code, collector_name="C", pickup_address="Desk", actor="test")
    biz.accept_collection(order.order_code, actor="test")
    biz.collect_sample(order.order_code, actor="test")
    biz.handover_sample(order.order_code, actor="test")
    db.session.commit()
    collection = BizCollection.query.filter_by(order_id=order.id).first()
    receive_sample(order_code=order.order_code, sample_code=collection.sample_code, received_by="Lab", actor="lab")
    create_accession(order_code=order.order_code, accessioned_by="Lab", actor="lab")
    enter_result_manual(
        order.order_code,
        test_code=catalog[0].code,
        result_value=value,
        reference_range="3.5-5.5",
        unit="mmol/L",
        abnormal_flag=flag,
        technician="tech.a",
        actor="lab",
    )
    if many > 1:
        res = BizResult.query.filter_by(order_id=order.id).first()
        for i in range(1, many):
            db.session.add(
                BizResultItem(
                    result_id=res.id,
                    test_code=f"T{i:03d}",
                    test_name=f"Extra Test {i} Viet Nam",
                    result_value=str(4.0 + (i % 3)),
                    unit="U/L",
                    reference_range="1-10",
                    flag="HIGH" if i % 5 == 0 else ("CRITICAL_HIGH" if i % 11 == 0 else "NORMAL"),
                    technician="tech.a",
                )
            )
        db.session.flush()
    mark_qc_passed(order.order_code, actor="lab")
    validate_result(order.order_code, actor="lab")
    db.session.commit()
    report = ensure_clinical_report(order)
    db.session.commit()
    return order, report, patient


class ProductionReportPdfTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.pdf_dir = Path(self._tmpdir.name)
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.tag = uuid.uuid4().hex[:6].upper()
        self.doctor = User(email=f"doc-{self.tag}@test.local", role="DOCTOR", password_hash="x", is_active=True)
        self.reception = User(email=f"rx-{self.tag}@test.local", role="RECEPTION", password_hash="x", is_active=True)
        self.patient_user = User(email=f"pt-{self.tag}@test.local", role="PATIENT", password_hash="x", is_active=True)
        self.collector = User(email=f"col-{self.tag}@test.local", role="COLLECTOR", password_hash="x", is_active=True)
        db.session.add_all([self.doctor, self.reception, self.patient_user, self.collector])
        db.session.commit()
        self.client = self.app.test_client()
        self._pdf_patch = mock.patch(
            "app.reporting_engine.pdf_service.default_pdf_storage_dir",
            return_value=self.pdf_dir,
        )
        self._pdf_patch.start()

    def tearDown(self):
        self._pdf_patch.stop()
        db.session.remove()
        try:
            db.drop_all()
        except Exception:
            pass
        self.ctx.pop()
        self._tmpdir.cleanup()

    def _session(self, user: User):
        with self.client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["email"] = user.email

    def test_normal_pdf_generation_and_content(self):
        order, report, _ = _seed_pending_review(self.tag + "N", flag="NORMAL", value="4.2")
        start_review(order.order_code, actor=self.doctor.email)
        approved = approve_report(order.order_code, doctor_note="On dinh", actor=self.doctor.email)
        db.session.commit()
        self.assertEqual(approved["report_status"], "approved")
        refreshed = ClinicalReport.query.filter_by(report_code=report.report_code).first()
        self.assertTrue(refreshed.pdf_path)
        pdf_bytes = Path(refreshed.pdf_path).read_bytes()
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 1500)
        # Metadata + HTML are authoritative for snapshot/content validation (PDF streams are compressed).
        self.assertIn(REPORT_PDF_TEMPLATE_ID.encode(), pdf_bytes)
        self.assertIn(REPORT_PDF_TEMPLATE_VERSION.encode(), pdf_bytes)
        self.assertIn(report.report_code.encode(), pdf_bytes)
        html = refreshed.html_content or ""
        self.assertIn(report.report_code, html)
        self.assertIn("Diagnostic Laboratory Report", html)
        self.assertIn(order.order_code, html)
        self.assertIn(REPORT_PDF_TEMPLATE_VERSION, html)

    def test_abnormal_and_critical_banners(self):
        order, report, _ = _seed_pending_review(self.tag + "C", flag="critical_high", value="999")
        approve_report(order.order_code, doctor_note="Critical reviewed", actor=self.doctor.email)
        db.session.commit()
        refreshed = ClinicalReport.query.filter_by(report_code=report.report_code).first()
        self.assertTrue(refreshed.pdf_path and Path(refreshed.pdf_path).read_bytes().startswith(b"%PDF"))
        self.assertTrue(refreshed.html_content and "CRITICAL" in refreshed.html_content.upper())
        self.assertIn("flag-critical", refreshed.html_content)
        self.assertIn(REPORT_PDF_TEMPLATE_ID.encode(), Path(refreshed.pdf_path).read_bytes())

    def test_multipage_pdf(self):
        order, report, _ = _seed_pending_review(self.tag + "M", flag="NORMAL", many=40)
        approve_report(order.order_code, doctor_note="Multi", actor=self.doctor.email)
        db.session.commit()
        refreshed = ClinicalReport.query.filter_by(report_code=report.report_code).first()
        raw = Path(refreshed.pdf_path).read_bytes()
        # Multiple pages => multiple /Type /Page or showPage markers via page objects
        self.assertGreaterEqual(raw.count(b"/Type /Page"), 2)

    def test_amended_version_new_pdf(self):
        order, report, _ = _seed_pending_review(self.tag + "A")
        approve_report(order.order_code, doctor_note="v1", actor=self.doctor.email)
        db.session.commit()
        v1 = ClinicalReport.query.filter_by(report_code=report.report_code).first()
        v1_path = v1.pdf_path
        from app.models.clinical_report import CriticalResultAlert

        for alert in CriticalResultAlert.query.filter_by(order_id=order.id, status="new").all():
            acknowledge_critical(alert.id, actor=self.doctor.email)
        release_report(order.order_code, actor=self.doctor.email)
        db.session.commit()
        amended = create_report_amendment(report.report_code, reason="Sửa kết quả", actor=self.doctor.email)
        db.session.commit()
        self.assertGreaterEqual(amended["report_version"], 2)
        # Re-approve amended version
        approve_report(order.order_code, doctor_note="v2 corrected", actor=self.doctor.email)
        db.session.commit()
        v2 = ClinicalReport.query.filter_by(order_id=order.id).order_by(ClinicalReport.report_version.desc()).first()
        self.assertEqual(v2.report_version, amended["report_version"])
        self.assertTrue(v2.pdf_path)
        self.assertNotEqual(v2.pdf_path, v1_path)
        self.assertTrue(v2.html_content and "AMENDED" in v2.html_content.upper())

    def test_authorization_gates(self):
        order, report, patient = _seed_pending_review(self.tag + "Z")
        # Pending: no PDF
        with self.assertRaises(ReportingEngineError):
            get_report_pdf(report.report_code, actor=self.doctor.email)
        self._session(self.collector)
        resp = self.client.get(f"/api/v1/reporting/reports/{report.report_code}/pdf")
        self.assertIn(resp.status_code, (401, 403))

        approve_report(order.order_code, doctor_note="ok", actor=self.doctor.email)
        db.session.commit()
        self._session(self.doctor)
        ok = self.client.get(f"/api/v1/reporting/reports/{report.report_code}/pdf")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.mimetype, "application/pdf")
        self.assertTrue(ok.data.startswith(b"%PDF"))

        # Patient cannot download until released
        self._session(self.patient_user)
        denied = self.client.get(f"/api/v1/reporting/patient/{patient.patient_code}/reports/{report.report_code}/pdf")
        self.assertIn(denied.status_code, (403, 400, 404))

    def test_missing_data_blocks_pdf(self):
        payload = {
            "patient": {"full_name": "X", "patient_code": "P"},
            "order": {"order_code": "O"},
            "collection": {},
            "accession": {},
            "items": [],
            "laboratory": {"name": "Lab"},
            "organization": {"name": "Org"},
            "abnormal_count": 0,
            "critical_count": 0,
        }
        # Empty items still render at PDF layer; service layer rejects
        order, report, _ = _seed_pending_review(self.tag + "E")
        from app.models.biz_order import BizResult

        res = BizResult.query.filter_by(order_id=order.id).first()
        for item in list(res.items):
            db.session.delete(item)
        db.session.commit()
        with self.assertRaises(ReportingEngineError):
            approve_report(order.order_code, doctor_note="empty", actor=self.doctor.email)

        # Direct renderer still returns valid PDF for empty (used only when service allows)
        data = build_frozen_pdf_document(
            payload=payload,
            report_code="RPT-TEST",
            report_version=1,
            report_hash="abc",
            report_status="approved",
            approved_by="doc",
            approved_at="2026-01-01",
        )
        self.assertTrue(data.startswith(b"%PDF"))

    def test_pdf_generation_failure(self):
        order, report, _ = _seed_pending_review(self.tag + "F")
        with mock.patch(
            "app.reporting_engine.service.write_report_pdf",
            side_effect=ReportPdfError("disk full"),
        ):
            with self.assertRaises(ReportingEngineError) as ctx:
                approve_report(order.order_code, doctor_note="fail", actor=self.doctor.email)
            self.assertIn("PDF generation failed", str(ctx.exception))

    def test_reprint_same_bytes_and_audit(self):
        order, report, _ = _seed_pending_review(self.tag + "R")
        approve_report(order.order_code, doctor_note="ok", actor=self.doctor.email)
        db.session.commit()
        first = get_report_pdf(report.report_code, actor=self.doctor.email)
        second = get_report_pdf(report.report_code, actor=self.doctor.email, as_reprint=True)
        db.session.commit()
        self.assertEqual(first["bytes"], second["bytes"])
        self.assertEqual(second["reprint_number"], 1)
        self.assertTrue(second["immutable"])
        self._session(self.doctor)
        resp = self.client.post(f"/api/v1/reporting/reports/{report.report_code}/reprint")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("X-Report-Reprint"), "2")

    def test_verify_route_and_qr(self):
        order, report, _ = _seed_pending_review(self.tag + "V")
        approve_report(order.order_code, doctor_note="ok", actor=self.doctor.email)
        db.session.commit()
        refreshed = ClinicalReport.query.filter_by(report_code=report.report_code).first()
        verified = verify_clinical_report(report.report_code, hash_prefix=refreshed.report_hash[:16])
        self.assertTrue(verified["valid"])
        bad = verify_clinical_report(report.report_code, hash_prefix="deadbeef")
        self.assertFalse(bad["valid"])
        page = self.client.get(f"/results/verify/report/{report.report_code}")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"VERIFIED", page.data)
        api = self.client.get(f"/api/v1/reporting/verify/{report.report_code}")
        self.assertEqual(api.status_code, 200)
        self.assertTrue(api.get_json()["success"])

    def test_immutable_finalized_version(self):
        order, report, _ = _seed_pending_review(self.tag + "I")
        approve_report(order.order_code, doctor_note="final", actor=self.doctor.email)
        db.session.commit()
        refreshed = ClinicalReport.query.filter_by(report_code=report.report_code).first()
        original = Path(refreshed.pdf_path).read_bytes()
        # Second write_report_pdf with same path must not overwrite
        path = write_report_pdf(
            payload=biz and {
                "patient": {"full_name": "Tampered"},
                "order": {"order_code": order.order_code},
                "collection": {},
                "accession": {},
                "items": [{"test_name": "X", "result_value": "1", "unit": "", "reference_range": "", "flag": "NORMAL"}],
                "laboratory": {"name": "Lab"},
                "organization": {"name": "Org"},
                "abnormal_count": 0,
                "critical_count": 0,
            },
            report_code=refreshed.report_code,
            report_version=refreshed.report_version,
            report_hash="tampered",
            report_status="approved",
            approved_by="evil",
            approved_at="2026-01-01",
            dest_path=refreshed.pdf_path,
        )
        self.assertEqual(Path(path).read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
