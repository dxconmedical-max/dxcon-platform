#!/usr/bin/env python3
"""Verify Laboratory Workflow — receive through medical validation."""

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
    lines = [
        ln
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith("--")
    ]
    for stmt in " ".join(lines).split(";"):
        stmt = stmt.strip()
        if stmt:
            try:
                db.session.execute(db.text(stmt))
            except Exception:
                db.session.rollback()
    db.session.commit()


def _advance_to_transit(biz, order_code: str, actor: str) -> None:
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
    from app.business_engine.statuses import ORDER_APPROVED, ORDER_LAB_RECEIVED, ORDER_PENDING_REVIEW
    from app.core.passwords import hash_password
    from app.extensions.db import db
    from app.lab_workspace.service import (
        assign_processing,
        create_accession,
        enter_result_manual,
        get_order_workspace,
        medical_validate,
        receive_sample,
        start_processing,
        status_contract,
        validate_result,
    )
    from app.models.audit_log import AuditLog
    from app.models.user import User

    start = time.time()
    checks: dict = {}
    app = create_app()
    GENERATED.mkdir(parents=True, exist_ok=True)
    run_tag = uuid.uuid4().hex[:6].upper()

    with app.app_context():
        if is_pg:
            apply_migration(db, "006_lab_workspace.sql")
            apply_migration(db, "007_lab_workflow.sql")
        else:
            db.create_all()

        user = User.query.filter(User.role.in_(["LAB", "ADMIN", "SUPER_ADMIN"])).first()
        if not user:
            user = User(
                email=f"lab-wf-{run_tag}@dxcon.test",
                role="LAB",
                password_hash=hash_password("VerifyOnly123!"),
                is_active=True,
            )
            db.session.add(user)
            db.session.commit()

        doctor = User.query.filter_by(role="DOCTOR").first()
        if not doctor:
            doctor = User(
                email=f"doc-wf-{run_tag}@dxcon.test",
                role="DOCTOR",
                password_hash=hash_password("VerifyOnly123!"),
                is_active=True,
            )
            db.session.add(doctor)
            db.session.commit()

        biz.ensure_test_catalog_seed()
        catalog = biz.ensure_test_catalog_seed()[0]
        patient = biz.create_patient(
            full_name=f"Lab WF Patient {run_tag}",
            phone=f"09{run_tag[:8]}",
            actor="verify@dxcon.test",
        )
        order = biz.create_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[catalog.id],
            actor="verify@dxcon.test",
        )
        biz.mark_order_paid(order.order_code, payment_method="cash", actor="verify@dxcon.test")
        _advance_to_transit(biz, order.order_code, "verify@dxcon.test")
        db.session.commit()

        contract = status_contract()
        checks["status_contract"] = {
            "ok": contract.get("accession_id_format") == "ACC-YYYYMMDD-000001"
            and "lab_received" in contract.get("order_flow", [])
        }

        recv = receive_sample(
            order_code=order.order_code,
            received_by="Lab Tech",
            condition_status="acceptable",
            actor="verify@dxcon.test",
        )
        db.session.commit()
        checks["receive"] = {"ok": recv.get("status") == ORDER_LAB_RECEIVED}

        acc = create_accession(order_code=order.order_code, accessioned_by="Lab Tech", actor="verify@dxcon.test")
        db.session.commit()
        checks["accession"] = {
            "ok": str(acc.get("accession_number", "")).startswith("ACC-"),
            "accession_number": acc.get("accession_number"),
        }

        assign_processing(
            order_code=order.order_code,
            bench_id="BENCH-1",
            instrument_id="INST-1",
            technician="tech.verify",
            actor="verify@dxcon.test",
        )
        start_processing(order_code=order.order_code, actor="verify@dxcon.test")
        db.session.commit()
        checks["processing"] = {"ok": True}

        entered = enter_result_manual(
            order.order_code,
            test_code=catalog.code,
            result_value="4.8",
            unit="mmol/L",
            reference_range="3.5-5.5",
            critical_low=2.0,
            critical_high=8.0,
            actor="verify@dxcon.test",
        )
        db.session.commit()
        checks["result_entry"] = {"ok": entered.get("result") is not None, "flag": entered.get("flag")}

        tech = validate_result(order.order_code, actor="verify@dxcon.test")
        db.session.commit()
        checks["technical_validation"] = {
            "ok": tech.get("status") == ORDER_PENDING_REVIEW and tech.get("locked") is True
        }

        med = medical_validate(order.order_code, doctor_note="Verified", actor=doctor.email)
        db.session.commit()
        checks["medical_validation"] = {"ok": med.get("status") == ORDER_APPROVED and med.get("locked") is True}

        ws = get_order_workspace(order.order_code)
        checks["refresh_persistence"] = {
            "ok": ws.get("locked") is True and ws["order"]["status"] == ORDER_APPROVED
        }

        audit_count = AuditLog.query.filter(AuditLog.action.like("lab.%")).count()
        checks["audit"] = {"ok": audit_count >= 3, "count": audit_count}

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = user.id
                sess["role"] = user.role
                sess["email"] = user.email
            checks["api_dashboard"] = {
                "ok": client.get("/api/v1/lab/workspace/dashboard").status_code == 200
            }
            checks["api_status_contract"] = {
                "ok": client.get("/api/v1/lab/workspace/status-contract").status_code == 200
            }

        # Rejection path (separate order)
        order2 = biz.create_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[catalog.id],
            actor="verify@dxcon.test",
        )
        biz.mark_order_paid(order2.order_code, payment_method="cash", actor="verify@dxcon.test")
        _advance_to_transit(biz, order2.order_code, "verify@dxcon.test")
        rej = receive_sample(
            order_code=order2.order_code,
            received_by="Lab Tech",
            condition_status="rejected",
            rejection_reason="wrong_tube",
            note="wrong tube type",
            actor="verify@dxcon.test",
        )
        db.session.commit()
        checks["rejection"] = {"ok": rej.get("status") == "rejected" and rej.get("rejection_reason") == "wrong_tube"}

        passed = sum(1 for c in checks.values() if c.get("ok"))
        summary = {
            "module": "laboratory_workflow",
            "passed": passed,
            "total": len(checks),
            "checks": checks,
            "accession_number": checks.get("accession", {}).get("accession_number"),
            "elapsed": round(time.time() - start, 2),
            "generated_at": utc_now(),
            "report_pdf_blockers": [
                "Report PDF generation is out of scope for Laboratory Workflow (STOP after medical validation).",
                "reporting_engine HTML report exists; dedicated PDF renderer / template packaging not verified in this milestone.",
                "Patient portal release of PDF after medical validation is a Result & Report epic item.",
            ],
        }
        (GENERATED / "LABORATORY_WORKFLOW_VERIFY.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
        print(f"Laboratory Workflow Verify: {passed}/{len(checks)} PASS")
        for name, r in checks.items():
            print(f"  [{'PASS' if r.get('ok') else 'FAIL'}] {name}")
        if summary.get("accession_number"):
            print(f"  Accession: {summary['accession_number']}")
        return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
