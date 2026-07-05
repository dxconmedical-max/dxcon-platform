#!/usr/bin/env python3
"""Verify Laboratory Operational Workspace — Sprint 007."""

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
    from app.extensions.db import db
    from app.lab_workspace.flags import calculate_abnormal_flag
    from app.lab_workspace.service import (
        create_accession,
        enter_result_manual,
        lab_security_report,
        lab_workspace_report,
        mark_qc_passed,
        receive_sample,
        validate_result,
        workspace_dashboard,
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
        else:
            db.create_all()

        user = User.query.filter(User.role.in_(["LAB", "ADMIN", "SUPER_ADMIN"])).first()
        if not user:
            user = User(email=f"lab-{run_tag}@dxcon.test", role="LAB", password_hash="x", is_active=True)
            db.session.add(user)
            db.session.commit()

        biz.ensure_test_catalog_seed()
        catalog = biz.ensure_test_catalog_seed()[0]
        patient = biz.create_patient(full_name=f"Lab Patient {run_tag}", phone=f"09{run_tag[:8]}", actor="verify@dxcon.test")
        order = biz.create_order(patient_code=patient.patient_code, test_catalog_ids=[catalog.id], actor="verify@dxcon.test")
        biz.mark_order_paid(order.order_code, payment_method="cash", actor="verify@dxcon.test")
        _advance_order_to_lab(biz, order.order_code, "verify@dxcon.test")
        db.session.commit()
        from app.models.biz_order import BizCollection, BizOrder

        collection = BizCollection.query.filter_by(order_id=order.id).first()

        recv = receive_sample(
            order_code=order.order_code,
            sample_code=collection.sample_code if collection else None,
            received_by="Lab Tech",
            condition_status="acceptable",
            actor="verify@dxcon.test",
        )
        db.session.commit()
        from app.business_engine.statuses import ORDER_LAB_RECEIVED

        checks["receive_sample"] = {
            "ok": recv.get("order_code") == order.order_code,
            "status": BizOrder.query.filter_by(order_code=order.order_code).first().status,
        }
        checks["receive_sample"]["ok"] = checks["receive_sample"]["ok"] and (
            BizOrder.query.filter_by(order_code=order.order_code).first().status == ORDER_LAB_RECEIVED
        )

        acc = create_accession(order_code=order.order_code, accessioned_by="Lab Tech", actor="verify@dxcon.test")
        db.session.commit()
        checks["accession"] = {"ok": acc.get("accession_number", "").startswith("ACC-")}

        entered = enter_result_manual(
            order.order_code,
            test_code=catalog.code,
            result_value="5.5",
            reference_range="3.5-5.5",
            actor="verify@dxcon.test",
        )
        db.session.commit()
        checks["result_entry"] = {"ok": entered.get("result") is not None}

        flag, _ = calculate_abnormal_flag("6.2", reference_range="3.5-5.5")
        checks["abnormal_flag"] = {"ok": flag == "high"}

        qc = mark_qc_passed(order.order_code, actor="verify@dxcon.test")
        db.session.commit()
        checks["qc_pass"] = {"ok": qc is not None}

        validated = validate_result(order.order_code, actor="verify@dxcon.test")
        db.session.commit()
        checks["lab_validation"] = {"ok": validated.get("status") == "pending_review"}

        audit_count = AuditLog.query.filter(AuditLog.action.like("lab.%")).count()
        checks["audit"] = {"ok": audit_count >= 1, "count": audit_count}

        dash = workspace_dashboard()
        checks["dashboard"] = {"ok": len(dash.get("widgets", [])) >= 8}

        ws_report = lab_workspace_report()
        sec_report = lab_security_report()
        (GENERATED / "LAB_WORKSPACE_REPORT.json").write_text(json.dumps(ws_report, indent=2), encoding="utf-8")
        (GENERATED / "LAB_SECURITY_REPORT.json").write_text(json.dumps(sec_report, indent=2), encoding="utf-8")

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = user.id
                sess["role"] = user.role
                sess["email"] = user.email
            checks["ui"] = {"ok": client.get("/app/lab").status_code == 200}
            checks["api"] = {"ok": client.get("/api/v1/lab/workspace/dashboard").status_code == 200}

        passed = sum(1 for c in checks.values() if c.get("ok"))
        summary = {"sprint": "007", "passed": passed, "total": len(checks), "checks": checks, "elapsed": round(time.time() - start, 2)}
        (GENERATED / "LAB_WORKSPACE_VERIFY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Lab Workspace Verify: {passed}/{len(checks)} PASS")
        for name, r in checks.items():
            print(f"  [{'PASS' if r.get('ok') else 'FAIL'}] {name}")
        return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
