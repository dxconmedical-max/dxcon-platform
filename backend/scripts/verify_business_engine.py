#!/usr/bin/env python3
"""Verify Production Business Engine Sprint 1 end-to-end workflow."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

GENERATED = ROOT / "generated_release"
REPORT_PATH = GENERATED / "BUSINESS_ENGINE_SPRINT1_REPORT.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    from app import create_app
    from app.business_engine import service as biz
    from app.business_engine.statuses import ORDER_RELEASED
    from app.extensions.db import db
    from app.models.biz_order import BizWorkflowAudit

    start = time.time()
    app = create_app()
    checks: dict = {}

    with app.app_context():
        db.create_all()
        biz.ensure_test_catalog_seed()
        db.session.commit()

        patient = biz.create_patient(
            full_name="Verify Patient Sprint1",
            phone=f"090{int(time.time()) % 10000000:07d}",
            national_id=f"NID{int(time.time())}",
            actor="verify@dxcon.test",
        )
        checks["create_patient"] = {"ok": bool(patient.patient_code), "patient_code": patient.patient_code}

        order = biz.create_order(patient_code=patient.patient_code, actor="verify@dxcon.test")
        biz.submit_order_for_payment(order.order_code, actor="verify@dxcon.test")
        checks["create_order"] = {
            "ok": bool(order.order_code) and len(order.items) > 0,
            "order_code": order.order_code,
            "item_count": len(order.items),
        }

        payment = biz.mark_order_paid(order.order_code, payment_method="cash", actor="verify@dxcon.test")
        checks["mark_paid"] = {"ok": payment.amount > 0, "receipt": payment.receipt_number}

        collection = biz.create_collection_job(
            order.order_code,
            collector_name="Verify Collector",
            pickup_address="123 Test St",
            actor="verify@dxcon.test",
        )
        checks["create_collection"] = {"ok": bool(collection.sample_code), "sample_code": collection.sample_code}

        biz.collect_sample(order.order_code, actor="verify@dxcon.test")
        biz.handover_sample(order.order_code, actor="verify@dxcon.test")
        biz.receive_sample_at_lab(order.order_code, received_by="Lab Verify", actor="verify@dxcon.test")

        items = [
            {
                "test_code": order.items[0].test_code,
                "test_name": order.items[0].test_name,
                "result_value": "13.2",
                "unit": "g/dL",
                "reference_range": "12-16",
            }
        ]
        result = biz.enter_results(order.order_code, items, actor="verify@dxcon.test")
        checks["enter_results"] = {"ok": bool(result.items), "result_code": result.result_code}

        biz.approve_result(order.order_code, doctor_note="Verified OK", actor="verify@dxcon.test")
        released = biz.release_report(order.order_code, actor="verify@dxcon.test")
        db.session.commit()

        final = biz.order_to_detail(order.order_code)
        audit_count = BizWorkflowAudit.query.count()
        order_audits = BizWorkflowAudit.query.filter_by(entity_type="order", entity_id=order.order_code).count()

        checks["release_report"] = {
            "ok": released.patient_visible and bool(released.html_content),
            "result_code": released.result_code,
        }
        checks["final_status_released"] = {
            "ok": final["status"] == ORDER_RELEASED,
            "status": final["status"],
        }
        checks["audit_logs"] = {
            "ok": audit_count >= 8 and order_audits >= 5,
            "total": audit_count,
            "order_audits": order_audits,
        }

        passed = sum(1 for item in checks.values() if item.get("ok"))
        total = len(checks)
        elapsed = round(time.time() - start, 2)

        report = {
            "sprint": "Production Business Engine Sprint 1",
            "generated_at": utc_now(),
            "elapsed_seconds": elapsed,
            "checks": checks,
            "summary": {"passed": passed, "total": total, "ok": passed == total},
            "sample_order_code": order.order_code,
            "sample_patient_code": patient.patient_code,
            "sample_result_code": released.result_code,
        }

        GENERATED.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

        print("\n=== DXCON BUSINESS ENGINE VERIFY ===\n")
        for name, item in checks.items():
            status = "PASS" if item.get("ok") else "FAIL"
            print(f"{status}: {name}")
        print(f"\nSummary: {passed}/{total} passed in {elapsed}s")
        print(f"Report: {REPORT_PATH}\n")

        return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
