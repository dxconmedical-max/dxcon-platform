#!/usr/bin/env python3
"""Verify Reporting Engine and Doctor Review — Sprint 008."""

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
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("DATABASE_URL", "sqlite:///:memory:")


def apply_migration(db, name: str) -> None:
    path = ROOT / "migrations" / name
    if not path.exists():
        return
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.strip().startswith("--")]
    for stmt in " ".join(lines).split(";"):
        stmt = stmt.strip()
        if stmt:
            db.session.execute(db.text(stmt))
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
    from app.business_engine.service import BusinessEngineError
    from app.extensions.db import db
    from app.lab_workspace.service import (
        create_accession,
        enter_result_manual,
        mark_qc_passed,
        receive_sample,
        validate_result,
    )
    from app.models.audit_log import AuditLog
    from app.models.biz_order import BizCollection, BizOrder
    from app.models.clinical_report import ClinicalReport, CriticalResultAlert, ReportDigitalSignature
    from app.models.user import User
    from app.reporting_engine.service import (
        ReportingEngineError,
        acknowledge_critical,
        approve_report,
        create_report_amendment,
        doctor_review_report,
        critical_result_report,
        ensure_clinical_report,
        patient_released_reports,
        release_report,
        report_security_report,
        reporting_engine_report,
        review_detail,
        review_queue,
        start_review,
    )

    start = time.time()
    checks: dict = {}
    app = create_app()
    GENERATED.mkdir(parents=True, exist_ok=True)
    run_tag = uuid.uuid4().hex[:6].upper()
    actor = "verify-reporting@dxcon.test"

    with app.app_context():
        if is_pg:
            apply_migration(db, "007_reporting_engine.sql")
        else:
            db.create_all()

        doctor = User.query.filter(User.role.in_(["DOCTOR", "ADMIN", "SUPER_ADMIN"])).first()
        if not doctor:
            doctor = User(email=f"doc-{run_tag}@dxcon.test", role="DOCTOR", password_hash="x", is_active=True)
            db.session.add(doctor)
            db.session.commit()

        lab_user = User.query.filter(User.role == "LAB").first()
        if not lab_user:
            lab_user = User(email=f"lab-{run_tag}@dxcon.test", role="LAB", password_hash="x", is_active=True)
            db.session.add(lab_user)
            db.session.commit()

        biz.ensure_test_catalog_seed()
        catalog = biz.ensure_test_catalog_seed()[0]
        patient = biz.create_patient(full_name=f"Report Patient {run_tag}", phone=f"08{run_tag[:8]}", actor=actor)
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
            result_value="999",
            reference_range="3.5-5.5",
            abnormal_flag="critical_high",
            actor=actor,
        )
        mark_qc_passed(order.order_code, actor=actor)
        validate_result(order.order_code, actor=actor)
        db.session.commit()

        report = ensure_clinical_report(order)
        db.session.commit()
        checks["pending_review_exists"] = {"ok": report.report_status == "pending_review"}

        queue = review_queue()
        checks["review_queue"] = {"ok": isinstance(queue.get("data"), list) and len(queue["data"]) >= 1}

        detail = review_detail(order.order_code)
        checks["review_detail"] = {"ok": detail.get("report", {}).get("report_code") == report.report_code}

        started = start_review(order.order_code, actor=actor)
        checks["start_review"] = {"ok": started.get("report_status") == "in_review"}

        approved = approve_report(order.order_code, doctor_note="Verified OK", actor=actor)
        db.session.commit()
        checks["approve_report"] = {"ok": approved.get("report_status") == "approved"}
        checks["report_hash"] = {"ok": bool(approved.get("report_hash"))}
        sig_count = ReportDigitalSignature.query.filter_by(report_id=report.id).count()
        checks["signature_foundation"] = {"ok": sig_count >= 1}

        release_blocked = False
        try:
            release_report(order.order_code, actor=actor)
        except ReportingEngineError:
            release_blocked = True
            db.session.rollback()
        checks["release_requires_ack"] = {"ok": release_blocked}

        alert = CriticalResultAlert.query.filter_by(order_id=order.id, status="new").first()
        checks["critical_alert"] = {"ok": alert is not None}
        if alert:
            acknowledge_critical(alert.id, actor=actor, note="Acknowledged in verify")
            db.session.commit()

        released = release_report(order.order_code, actor=actor)
        db.session.commit()
        checks["release_after_approval"] = {"ok": released.get("report_status") == "released"}

        visible = patient_released_reports(patient.patient_code)
        checks["patient_visible_released"] = {"ok": any(r["report_code"] == report.report_code for r in visible)}

        unreleased = ClinicalReport.query.filter(
            ClinicalReport.patient_id == patient.patient_code,
            ClinicalReport.report_status != "released",
        ).count()
        hidden = patient_released_reports(patient.patient_code)
        checks["patient_hidden_unreleased"] = {
            "ok": all(r["report_status"] == "released" for r in hidden),
            "unreleased_count": unreleased,
        }

        amended = create_report_amendment(report.report_code, reason="Correction", actor=actor)
        db.session.commit()
        checks["versioning"] = {"ok": amended.get("report_version", 0) >= 2}

        audit_count = AuditLog.query.filter(AuditLog.action.like("report.%")).count()
        checks["audit_logs"] = {"ok": audit_count >= 3, "count": audit_count}

        eng_report = reporting_engine_report()
        doc_report = doctor_review_report()
        sec_report = report_security_report()
        crit_report = critical_result_report()
        (GENERATED / "REPORTING_ENGINE_REPORT.json").write_text(json.dumps(eng_report, indent=2), encoding="utf-8")
        (GENERATED / "DOCTOR_REVIEW_REPORT.json").write_text(json.dumps(doc_report, indent=2), encoding="utf-8")
        (GENERATED / "REPORT_SECURITY_REPORT.json").write_text(json.dumps(sec_report, indent=2), encoding="utf-8")
        (GENERATED / "CRITICAL_RESULT_REPORT.json").write_text(json.dumps(crit_report, indent=2), encoding="utf-8")

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = doctor.id
                sess["role"] = doctor.role
                sess["email"] = doctor.email
            checks["ui_review_queue"] = {"ok": client.get("/app/doctor/review").status_code == 200}
            checks["ui_review_detail"] = {"ok": client.get(f"/app/doctor/review/{order.order_code}").status_code == 200}
            checks["ui_report_preview"] = {"ok": client.get(f"/app/reports/{report.report_code}/preview").status_code == 200}
            checks["api_queue"] = {"ok": client.get("/api/v1/reporting/review-queue").status_code == 200}

        passed = sum(1 for c in checks.values() if c.get("ok"))
        summary = {
            "sprint": "008",
            "passed": passed,
            "total": len(checks),
            "checks": checks,
            "elapsed": round(time.time() - start, 2),
            "generated_at": utc_now(),
        }
        (GENERATED / "REPORTING_ENGINE_VERIFY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Reporting Engine Verify: {passed}/{len(checks)} PASS")
        for name, r in checks.items():
            print(f"  [{'PASS' if r.get('ok') else 'FAIL'}] {name}")
        return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
