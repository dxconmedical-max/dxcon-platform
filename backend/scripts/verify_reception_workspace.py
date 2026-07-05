#!/usr/bin/env python3
"""Verify Reception Operational Workspace — Sprint 006."""

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


def main() -> int:
    database_url = load_database_url()
    os.environ["DATABASE_URL"] = database_url
    is_pg = database_url.startswith("postgresql") or database_url.startswith("postgres")

    from app import create_app
    from app.business_engine import service as biz
    from app.core.permissions import role_has_permission
    from app.extensions.db import db
    from app.models.audit_log import AuditLog
    from app.models.user import User
    from app.reception_workspace.security import RECEPTION_FORBIDDEN_ACTIONS
    from app.reception_workspace.service import (
        collect_payment,
        create_collection_after_payment,
        create_reception_order,
        duplicate_warnings,
        fast_search_patients,
        generate_barcodes,
        payment_report,
        queue_report,
        reception_workspace_report,
        register_patient,
        render_request_form,
        workspace_dashboard,
    )

    start = time.time()
    checks: dict = {}
    app = create_app()
    GENERATED.mkdir(parents=True, exist_ok=True)
    run_tag = uuid.uuid4().hex[:6].upper()

    with app.app_context():
        if is_pg:
            apply_migration(db, "005_reception_workspace.sql")
        else:
            db.create_all()

        user = User.query.filter(User.role.in_(["RECEPTION", "ADMIN", "SUPER_ADMIN"])).first()
        if not user:
            from werkzeug.security import generate_password_hash

            user = User(
                email=f"verify-reception-{run_tag}@dxcon.test",
                role="RECEPTION",
                password_hash=generate_password_hash("verify", method="pbkdf2:sha256"),
                is_active=True,
            )
            db.session.add(user)
            db.session.commit()

        biz.ensure_test_catalog_seed()
        db.session.commit()
        catalog = biz.ensure_test_catalog_seed()[0]

        # Duplicate detection
        phone = f"09{run_tag[:8]}"
        reg = register_patient(
            {
                "full_name": f"Reception Test {run_tag}",
                "phone": phone,
                "gender": "F",
                "date_of_birth": "1990-01-01",
                "address": "Test Address",
            },
            actor="verify@dxcon.test",
        )
        db.session.commit()
        checks["patient_registration"] = {"ok": reg.get("ok") is True, "patient_code": reg.get("patient", {}).get("patient_code")}
        patient_code = reg["patient"]["patient_code"]

        dup = duplicate_warnings(phone=phone)
        checks["duplicate_detection"] = {"ok": len(dup) >= 1}

        found = fast_search_patients(patient_code)
        checks["patient_search"] = {"ok": found["pagination"]["total"] >= 1}

        order_result = create_reception_order(
            patient_code=patient_code,
            test_catalog_ids=[catalog.id],
            actor="verify@dxcon.test",
        )
        db.session.commit()
        order_code = order_result["order"]["order_code"]
        checks["order_creation"] = {"ok": bool(order_code), "total": order_result["pricing"]["total"]}

        pay = collect_payment(order_code, payment_method="cash", actor="verify@dxcon.test")
        db.session.commit()
        checks["payment"] = {"ok": pay.get("payment") is not None}
        checks["invoice"] = {"ok": pay.get("invoice") is not None}

        barcodes = generate_barcodes(order_code)
        checks["barcode"] = {"ok": bool(barcodes.get("order_barcode"))}

        form_html = render_request_form(order_code)
        checks["print_request_form"] = {"ok": "Lab Request Form" in form_html}

        coll = create_collection_after_payment(order_code, actor="verify@dxcon.test")
        db.session.commit()
        checks["queue_collection"] = {"ok": coll.get("collection") is not None}

        dash = workspace_dashboard()
        checks["dashboard"] = {
            "ok": len(dash.get("widgets", [])) >= 8 and "kpis" in dash,
            "widgets": len(dash.get("widgets", [])),
        }
        checks["queue"] = {"ok": "workflow_queue" in dash}

        audit_count = AuditLog.query.filter(
            AuditLog.action.like("reception.%") | AuditLog.action.like("biz.%")
        ).count()
        checks["audit"] = {"ok": audit_count >= 1, "count": audit_count}

        checks["security"] = {
            "ok": role_has_permission("RECEPTION", "reception.write")
            and role_has_permission("RECEPTION", "payments.collect")
            and not role_has_permission("RECEPTION", "patient.delete"),
            "forbidden": list(RECEPTION_FORBIDDEN_ACTIONS),
        }

        ws_report = reception_workspace_report()
        pay_report = payment_report()
        q_report = queue_report()
        (GENERATED / "RECEPTION_WORKSPACE_REPORT.json").write_text(json.dumps(ws_report, indent=2), encoding="utf-8")
        (GENERATED / "PAYMENT_REPORT.json").write_text(json.dumps(pay_report, indent=2), encoding="utf-8")
        (GENERATED / "QUEUE_REPORT.json").write_text(json.dumps(q_report, indent=2), encoding="utf-8")

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = user.id
                sess["role"] = user.role
                sess["email"] = user.email
            ui_ok = client.get("/app/reception").status_code == 200
            queue_ok = client.get("/app/reception/queue").status_code == 200
            api_ok = client.get("/api/v1/reception/workspace/dashboard").status_code == 200
            checks["ui"] = {"ok": ui_ok and queue_ok, "reception": ui_ok, "queue": queue_ok}
            checks["api"] = {"ok": api_ok}

        passed = sum(1 for c in checks.values() if c.get("ok"))
        total = len(checks)
        elapsed = round(time.time() - start, 2)
        summary = {
            "sprint": "006",
            "module": "reception_workspace",
            "timestamp": utc_now(),
            "elapsed_seconds": elapsed,
            "passed": passed,
            "total": total,
            "checks": checks,
        }
        (GENERATED / "RECEPTION_WORKSPACE_VERIFY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

        print(f"Reception Workspace Verify: {passed}/{total} PASS ({elapsed}s)")
        for name, result in checks.items():
            print(f"  [{'PASS' if result.get('ok') else 'FAIL'}] {name}")
        return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
