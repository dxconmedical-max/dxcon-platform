#!/usr/bin/env python3
"""Verify Doctor Portal and Patient Portal — Sprint 009."""

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
            try:
                db.session.execute(db.text(stmt))
            except Exception:
                pass
    db.session.commit()


def main() -> int:
    database_url = load_database_url()
    os.environ["DATABASE_URL"] = database_url
    is_pg = database_url.startswith("postgresql") or database_url.startswith("postgres")

    from app import create_app
    from app.business_engine import service as biz
    from app.extensions.db import db
    from app.models.audit_log import AuditLog
    from app.models.user import User
    from app.doctor_portal.service import dashboard as doctor_dashboard, doctor_portal_report, portal_security_report, search_patients
    from app.patient_portal.service import (
        PatientPortalError,
        dashboard as patient_dashboard,
        generate_qr_health_card,
        grant_consent,
        list_notifications,
        medical_history,
        patient_portal_report,
    )
    from app.reporting_engine.service import approve_report, ensure_clinical_report, patient_released_reports, release_report

    start = time.time()
    checks: dict = {}
    app = create_app()
    GENERATED.mkdir(parents=True, exist_ok=True)
    run_tag = uuid.uuid4().hex[:6].upper()
    actor = "verify-portal@dxcon.test"

    with app.app_context():
        if is_pg:
            apply_migration(db, "007_reporting_engine.sql")
            apply_migration(db, "008_portal.sql")
        else:
            db.create_all()

        doctor = User.query.filter(User.role.in_(["DOCTOR", "ADMIN"])).first()
        if not doctor:
            doctor = User(email=f"doc-{run_tag}@dxcon.test", role="DOCTOR", password_hash="x", is_active=True)
            db.session.add(doctor)
        patient_user = User.query.filter_by(role="PATIENT").first()
        if not patient_user:
            patient_user = User(email=f"pat-{run_tag}@dxcon.test", role="PATIENT", password_hash="x", is_active=True)
            db.session.add(patient_user)
        db.session.commit()

        biz.ensure_test_catalog_seed()
        catalog = biz.ensure_test_catalog_seed()[0]
        patient = biz.create_patient(full_name=f"Portal Patient {run_tag}", phone=f"07{run_tag[:8]}", actor=actor)
        order = biz.create_order(patient_code=patient.patient_code, test_catalog_ids=[catalog.id], actor=actor)
        biz.mark_order_paid(order.order_code, payment_method="cash", actor=actor)
        db.session.commit()

        from app.lab_workspace.service import create_accession, enter_result_manual, mark_qc_passed, receive_sample, validate_result as lab_validate

        biz.create_collection_job(order.order_code, collector_name="C", pickup_address="X", actor=actor)
        biz.accept_collection(order.order_code, actor=actor)
        biz.collect_sample(order.order_code, actor=actor)
        biz.handover_sample(order.order_code, actor=actor)
        db.session.commit()
        from app.models.biz_order import BizCollection

        coll = BizCollection.query.filter_by(order_id=order.id).first()
        receive_sample(order_code=order.order_code, sample_code=coll.sample_code if coll else None, received_by="T", actor=actor)
        create_accession(order_code=order.order_code, accessioned_by="T", actor=actor)
        enter_result_manual(order.order_code, test_code=catalog.code, result_value="5.0", reference_range="3-7", actor=actor)
        mark_qc_passed(order.order_code, actor=actor)
        lab_validate(order.order_code, actor=actor)
        report = ensure_clinical_report(order)
        approve_report(order.order_code, doctor_note="OK", actor=actor)
        release_report(order.order_code, actor=actor)
        db.session.commit()

        checks["doctor_dashboard"] = {"ok": "widgets" in doctor_dashboard(doctor_id=doctor.id, actor=actor)}
        checks["patient_search"] = {"ok": isinstance(search_patients(q=patient.patient_code).get("data"), list)}
        checks["report_visibility"] = {"ok": any(r["report_code"] == report.report_code for r in patient_released_reports(patient.patient_code))}

        try:
            with app.test_request_context():
                from flask import session
                session["role"] = "PATIENT"
                session["patient_code"] = patient.patient_code
                patient_dashboard(patient_code=patient.patient_code, actor=actor)
            checks["patient_dashboard"] = {"ok": True}
        except PatientPortalError as exc:
            checks["patient_dashboard"] = {"ok": False, "error": str(exc)}

        with app.test_request_context():
            from flask import session
            session["role"] = "PATIENT"
            session["patient_code"] = patient.patient_code
            checks["invoice_visibility"] = {"ok": "invoices" in medical_history(patient_code=patient.patient_code)}
            consent = grant_consent("portal_access", patient_code=patient.patient_code, actor=actor)
            checks["consent"] = {"ok": consent.get("status") == "GRANTED"}
            qr = generate_qr_health_card(patient_code=patient.patient_code, actor=actor)
            checks["qr"] = {"ok": bool(qr.get("verification_token"))}
        db.session.commit()

        from app.models.portal import PortalNotification

        db.session.add(
            PortalNotification(
                recipient_type="patient",
                recipient_id=patient.patient_code,
                event_type="report_released",
                channel="IN_APP",
                title="Report ready",
                body="Your report is available",
            )
        )
        db.session.commit()
        with app.test_request_context():
            from flask import session
            session["role"] = "PATIENT"
            session["patient_code"] = patient.patient_code
            checks["notification"] = {"ok": len(list_notifications(patient_code=patient.patient_code).get("data", [])) >= 1}

        sec = portal_security_report()
        checks["security"] = {"ok": sec.get("patient_isolation") is True}
        checks["audit"] = {"ok": AuditLog.query.filter(AuditLog.action.like("portal.%")).count() >= 1}

        doc_report = doctor_portal_report()
        pat_report = patient_portal_report()
        (GENERATED / "DOCTOR_PORTAL_REPORT.json").write_text(json.dumps(doc_report, indent=2), encoding="utf-8")
        (GENERATED / "PATIENT_PORTAL_REPORT.json").write_text(json.dumps(pat_report, indent=2), encoding="utf-8")
        (GENERATED / "PORTAL_SECURITY_REPORT.json").write_text(json.dumps(sec, indent=2), encoding="utf-8")

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = doctor.id
                sess["role"] = doctor.role
                sess["email"] = doctor.email
            checks["doctor_login_ui"] = {"ok": client.get("/app/doctor/dashboard").status_code == 200}
            checks["doctor_search_ui"] = {"ok": client.get("/app/doctor/patients").status_code == 200}
            with client.session_transaction() as sess:
                sess["user_id"] = patient_user.id
                sess["role"] = "PATIENT"
                sess["email"] = patient_user.email
                sess["patient_code"] = patient.patient_code
            checks["patient_login_ui"] = {"ok": client.get("/app/patient/dashboard").status_code == 200}
            checks["patient_reports_ui"] = {"ok": client.get("/app/patient/reports").status_code == 200}
            with client.session_transaction() as sess:
                sess["user_id"] = doctor.id
                sess["role"] = doctor.role
                sess["email"] = doctor.email
            checks["api_doctor"] = {"ok": client.get("/api/v1/portal/doctor/dashboard").status_code == 200}

        passed = sum(1 for c in checks.values() if c.get("ok"))
        summary = {"sprint": "009", "passed": passed, "total": len(checks), "checks": checks, "elapsed": round(time.time() - start, 2), "generated_at": utc_now()}
        (GENERATED / "PORTAL_VERIFY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Portal Verify: {passed}/{len(checks)} PASS")
        for name, r in checks.items():
            print(f"  [{'PASS' if r.get('ok') else 'FAIL'}] {name}")
        return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
