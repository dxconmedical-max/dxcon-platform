#!/usr/bin/env python3
"""Verify Production Report PDF — finalized clinical PDF generation."""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated_release"
ENV_FILE = ROOT / ".env"
sys.path.insert(0, str(ROOT))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_database_url() -> str:
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "sqlite:///:memory:"


def apply_migration(db, name: str) -> None:
    path = ROOT / "migrations" / name
    if not path.exists():
        return
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.strip().startswith("--")]
    for stmt in " ".join(lines).split(";"):
        stmt = stmt.strip()
        if stmt:
            try:
                db.session.execute(db.text(stmt))
            except Exception:
                db.session.rollback()
    db.session.commit()


def _advance_order_to_lab(biz, order_code: str, actor: str) -> None:
    biz.create_collection_job(order_code, collector_name="Verify Collector", pickup_address="Desk", actor=actor)
    biz.accept_collection(order_code, actor=actor)
    biz.collect_sample(order_code, actor=actor)
    biz.handover_sample(order_code, actor=actor)


def main() -> int:
    database_url = load_database_url()
    os.environ["DATABASE_URL"] = database_url
    is_pg = database_url.startswith("postgresql") or database_url.startswith("postgres")

    from app import create_app
    from app.business_engine import service as biz
    from app.core.passwords import hash_password
    from app.extensions.db import db
    from app.lab_workspace.service import (
        create_accession,
        enter_result_manual,
        mark_qc_passed,
        receive_sample,
        validate_result,
    )
    from app.models.biz_order import BizCollection
    from app.models.clinical_report import ClinicalReport, CriticalResultAlert
    from app.models.user import User
    from app.reporting_engine.pdf_service import REPORT_PDF_TEMPLATE_ID, REPORT_PDF_TEMPLATE_VERSION
    from app.reporting_engine.service import (
        acknowledge_critical,
        approve_report,
        create_report_amendment,
        ensure_clinical_report,
        get_report_pdf,
        production_report_pdf_report,
        release_report,
        start_review,
        verify_clinical_report,
    )

    start = time.time()
    checks: dict = {}
    app = create_app()
    GENERATED.mkdir(parents=True, exist_ok=True)
    run_tag = uuid.uuid4().hex[:6].upper()
    actor = "verify-report-pdf@dxcon.test"

    with app.app_context():
        if is_pg:
            apply_migration(db, "007_reporting_engine.sql")
        else:
            db.create_all()

        doctor = User.query.filter(User.role.in_(["DOCTOR", "ADMIN", "SUPER_ADMIN"])).first()
        if not doctor:
            doctor = User(
                email=f"doc-pdf-{run_tag}@dxcon.test",
                role="DOCTOR",
                password_hash=hash_password("VerifyOnly123!"),
                is_active=True,
            )
            db.session.add(doctor)
            db.session.commit()

        biz.ensure_test_catalog_seed()
        catalog = biz.ensure_test_catalog_seed()[0]
        patient = biz.create_patient(full_name=f"PDF Patient {run_tag}", phone=f"08{run_tag[:8]}", actor=actor)
        order = biz.create_order(patient_code=patient.patient_code, test_catalog_ids=[catalog.id], actor=actor)
        biz.mark_order_paid(order.order_code, payment_method="cash", actor=actor)
        _advance_order_to_lab(biz, order.order_code, actor)
        db.session.commit()

        collection = BizCollection.query.filter_by(order_id=order.id).first()
        receive_sample(
            order_code=order.order_code,
            sample_code=collection.sample_code if collection else None,
            received_by="Lab Tech",
            condition_status="acceptable",
            actor=actor,
        )
        create_accession(order_code=order.order_code, accessioned_by="Lab Tech", actor=actor)
        enter_result_manual(
            order.order_code,
            test_code=catalog.code,
            result_value="4.5",
            reference_range="3.5-5.5",
            unit="mmol/L",
            abnormal_flag="NORMAL",
            technician="verify.tech",
            actor=actor,
        )
        mark_qc_passed(order.order_code, actor=actor)
        validate_result(order.order_code, actor=actor)
        db.session.commit()

        report = ensure_clinical_report(order)
        db.session.commit()
        checks["pending_has_no_pdf"] = {"ok": not report.pdf_path}

        start_review(order.order_code, actor=actor)
        approved = approve_report(order.order_code, doctor_note="PDF verify OK", actor=actor)
        db.session.commit()
        report = ClinicalReport.query.filter_by(report_code=report.report_code).first()
        checks["approved_status"] = {"ok": report.report_status == "approved"}
        checks["pdf_path_set"] = {"ok": bool(report.pdf_path)}
        pdf_ok = False
        synthetic_id = report.report_code
        if report.pdf_path and Path(report.pdf_path).exists():
            data = Path(report.pdf_path).read_bytes()
            pdf_ok = data.startswith(b"%PDF") and REPORT_PDF_TEMPLATE_ID.encode() in data
        checks["pdf_bytes_valid"] = {"ok": pdf_ok}
        checks["html_aligned"] = {
            "ok": bool(report.html_content)
            and report.report_code in (report.html_content or "")
            and REPORT_PDF_TEMPLATE_VERSION in (report.html_content or "")
        }
        checks["hash_and_qr"] = {"ok": bool(report.report_hash) and bool(report.qr_payload)}

        bundle = get_report_pdf(report.report_code, actor=actor)
        checks["download_pdf"] = {"ok": bundle["bytes"].startswith(b"%PDF") and bundle["immutable"]}
        reprint = get_report_pdf(report.report_code, actor=actor, as_reprint=True)
        db.session.commit()
        checks["reprint_same_bytes"] = {
            "ok": reprint["bytes"] == bundle["bytes"] and reprint["reprint_number"] == 1
        }

        verified = verify_clinical_report(report.report_code, hash_prefix=(report.report_hash or "")[:16])
        checks["verify_valid"] = {"ok": verified.get("valid") is True}

        for alert in CriticalResultAlert.query.filter_by(order_id=order.id, status="new").all():
            acknowledge_critical(alert.id, actor=actor)
        released = release_report(order.order_code, actor=actor)
        db.session.commit()
        checks["release_requires_pdf"] = {"ok": released.get("report_status") == "released"}

        amended = create_report_amendment(report.report_code, reason="Correction verify", actor=actor)
        db.session.commit()
        approve_report(order.order_code, doctor_note="Amended PDF", actor=actor)
        db.session.commit()
        v2 = ClinicalReport.query.filter_by(order_id=order.id).order_by(ClinicalReport.report_version.desc()).first()
        checks["amended_pdf"] = {
            "ok": amended.get("report_version", 0) >= 2
            and bool(v2.pdf_path)
            and v2.pdf_path != report.pdf_path
        }

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = doctor.id
                sess["role"] = doctor.role
                sess["email"] = doctor.email
            api_pdf = client.get(f"/api/v1/reporting/reports/{synthetic_id}/pdf")
            checks["api_pdf_auth"] = {
                "ok": api_pdf.status_code == 200 and api_pdf.data.startswith(b"%PDF")
            }
            verify_page = client.get(f"/results/verify/report/{synthetic_id}")
            checks["verify_page"] = {"ok": verify_page.status_code == 200 and b"VERIFIED" in verify_page.data}
            unauth = app.test_client().get(f"/api/v1/reporting/reports/{synthetic_id}/pdf")
            checks["api_pdf_unauthorized"] = {"ok": unauth.status_code in (401, 403)}

        summary_report = production_report_pdf_report()
        (GENERATED / "PRODUCTION_REPORT_PDF_REPORT.json").write_text(
            json.dumps(summary_report, indent=2), encoding="utf-8"
        )

        passed = sum(1 for c in checks.values() if c.get("ok"))
        summary = {
            "feature": "PRODUCTION_REPORT_PDF",
            "template_id": REPORT_PDF_TEMPLATE_ID,
            "template_version": REPORT_PDF_TEMPLATE_VERSION,
            "synthetic_report_id": synthetic_id,
            "passed": passed,
            "total": len(checks),
            "checks": checks,
            "elapsed": round(time.time() - start, 2),
            "generated_at": utc_now(),
            "dashboard_e2e_blockers": [
                "Clinical Dashboard aggregations not verified in this milestone.",
                "End-to-end browser PDF download UX in apps/web not wired in this milestone.",
                "Patient portal PDF deep-link beyond API route not verified in this milestone.",
            ],
        }
        (GENERATED / "PRODUCTION_REPORT_PDF_VERIFY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Production Report PDF Verify: {passed}/{len(checks)} PASS")
        print(f"  template={REPORT_PDF_TEMPLATE_ID}@{REPORT_PDF_TEMPLATE_VERSION}")
        print(f"  synthetic_report_id={synthetic_id}")
        for name, r in checks.items():
            print(f"  [{'PASS' if r.get('ok') else 'FAIL'}] {name}")
        return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
