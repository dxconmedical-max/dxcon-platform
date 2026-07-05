#!/usr/bin/env python3
"""Verify LIS Integration Foundation — Sprint 007."""

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


def main() -> int:
    database_url = load_database_url()
    os.environ["DATABASE_URL"] = database_url
    is_pg = database_url.startswith("postgresql") or database_url.startswith("postgres")

    from app import create_app
    from app.business_engine import service as biz
    from app.extensions.db import db
    from app.lab_workspace.lis_service import import_csv, import_json, lis_integration_report, list_failed_imports, upsert_connector
    from app.models.audit_log import AuditLog
    from app.models.biz_order import BizResult
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

        conn = upsert_connector(
            {"connector_code": f"LIS-{run_tag}", "connector_name": "Verify LIS", "connector_type": "CSV_UPLOAD"},
            actor="verify@dxcon.test",
        )
        db.session.commit()
        checks["connector_crud"] = {"ok": conn.get("connector_code") == f"LIS-{run_tag}"}

        biz.ensure_test_catalog_seed()
        catalog = biz.ensure_test_catalog_seed()[0]
        patient = biz.create_patient(full_name=f"LIS Patient {run_tag}", phone=f"08{run_tag[:8]}", actor="verify@dxcon.test")
        order = biz.create_order(patient_code=patient.patient_code, test_catalog_ids=[catalog.id], actor="verify@dxcon.test")
        biz.mark_order_paid(order.order_code, payment_method="cash", actor="verify@dxcon.test")
        from app.models.biz_order import BizCollection

        biz.create_collection_job(order.order_code, collector_name="C", pickup_address="D", actor="verify@dxcon.test")
        biz.accept_collection(order.order_code, actor="verify@dxcon.test")
        biz.collect_sample(order.order_code, actor="verify@dxcon.test")
        biz.handover_sample(order.order_code, actor="verify@dxcon.test")
        biz.receive_sample_at_lab(order.order_code, received_by="Lab", actor="verify@dxcon.test")
        coll = BizCollection.query.filter_by(order_id=order.id).first()
        db.session.commit()

        csv_row = (
            f"patient_code,order_code,sample_code,test_code,value,unit,reference_range\n"
            f"{patient.patient_code},{order.order_code},{coll.sample_code},{catalog.code},4.2,mg/dL,3.5-5.5\n"
        )
        batch = import_csv(csv_row.encode(), connector_id=conn["id"], actor="verify@dxcon.test")
        db.session.commit()
        checks["csv_import"] = {"ok": batch.get("success_rows", 0) >= 1}

        result = BizResult.query.filter_by(order_id=order.id).first()
        checks["import_requires_validation"] = {
            "ok": result is not None and result.workflow_status == "validation_required" and result.result_source == "imported",
        }
        checks["no_auto_release"] = {"ok": result is not None and result.status != "released"}

        dup_batch = import_csv(csv_row.encode(), connector_id=conn["id"], actor="verify@dxcon.test")
        db.session.commit()
        checks["duplicate_rejection"] = {"ok": dup_batch.get("failed_rows", 0) >= 1}

        bad_csv = b"patient_code,order_code,test_code,value\nNOPE,NOPE,CBC,1.0\n"
        bad_batch = import_csv(bad_csv, connector_id=conn["id"], actor="verify@dxcon.test")
        db.session.commit()
        checks["missing_patient_rejection"] = {"ok": bad_batch.get("failed_rows", 0) >= 1}

        json_batch = import_json(
            [{"patient_code": patient.patient_code, "order_code": "NO-SUCH-ORDER", "test_code": catalog.code, "value": "1"}],
            connector_id=conn["id"],
            actor="verify@dxcon.test",
        )
        db.session.commit()
        checks["missing_order_rejection"] = {"ok": json_batch.get("failed_rows", 0) >= 1}

        json_bad_test = import_json(
            [{"patient_code": patient.patient_code, "order_code": order.order_code, "test_code": "NOTINMDM", "value": "1"}],
            connector_id=conn["id"],
            actor="verify@dxcon.test",
        )
        db.session.commit()
        checks["missing_test_rejection"] = {"ok": json_bad_test.get("failed_rows", 0) >= 1}

        failed = list_failed_imports()
        checks["failed_imports_table"] = {"ok": len(failed) >= 1}

        audit_count = AuditLog.query.filter(AuditLog.action.like("lab.%")).count()
        checks["audit"] = {"ok": audit_count >= 1}

        lis_report = lis_integration_report()
        (GENERATED / "LIS_INTEGRATION_REPORT.json").write_text(json.dumps(lis_report, indent=2), encoding="utf-8")

        passed = sum(1 for c in checks.values() if c.get("ok"))
        print(f"LIS Integration Verify: {passed}/{len(checks)} PASS")
        for name, r in checks.items():
            print(f"  [{'PASS' if r.get('ok') else 'FAIL'}] {name}")
        return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
