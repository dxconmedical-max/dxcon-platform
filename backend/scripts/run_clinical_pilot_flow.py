#!/usr/bin/env python3
"""End-to-end clinical pilot flow (SIMULATED) — development and test only."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("ANALYZER_SIMULATOR_ENABLED", "true")


def simulator_allowed() -> bool:
    if os.environ.get("FLASK_ENV") == "production" or os.environ.get("ENVIRONMENT") == "production":
        return os.environ.get("CLINICAL_PILOT_SIMULATOR_ENABLED", "").lower() == "true"
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Clinical pilot flow (SIMULATED)")
    parser.add_argument("--organization-id", default="pilot-org")
    args = parser.parse_args()

    if not simulator_allowed():
        print("ERROR: Clinical pilot simulator disabled in production.")
        return 1

    from app import create_app
    from app.analyzer_integration.service import create_test_mapping, ingest_result_message, register_analyzer
    from app.clinical_governance.service import promote_preliminary_to_result, release_report_governed, validate_result_item
    from app.extensions.db import db
    from app.models.biz_order import BizOrder, BizResult
    from app.models.clinical_report import ClinicalReport
    from app.business_engine.statuses import ORDER_PENDING_REVIEW, RESULT_PENDING_REVIEW
    from app.reporting_engine.service import approve_report, ensure_clinical_report

    app = create_app()
    steps: list[dict] = []
    with app.app_context():
        db.create_all()
        org = args.organization_id

        order = BizOrder(
            order_code=f"ORD-PILOT-{uuid.uuid4().hex[:6].upper()}",
            patient_code="SIM-PAT-001",
            patient_name="SIM Patient",
            status="testing",
        )
        db.session.add(order)
        db.session.commit()
        steps.append({"step": 1, "action": "create_order", "order_code": order.order_code, "label": "SIMULATED"})

        anz = register_analyzer({"name": "Pilot Sim", "protocol": "SIMULATOR"}, organization_id=org)
        create_test_mapping(
            {"analyzer_test_code": "GLU", "dxcon_test_code": "GLUCOSE", "unit": "mg/dL"},
            organization_id=org,
            actor="pilot@test",
        )
        db.session.commit()

        prelim = ingest_result_message(
            {"specimen_barcode": "DX-PILOT-001", "analyzer_test_code": "GLU", "value": "98", "unit": "mg/dL"},
            organization_id=org,
            analyzer_id=anz["id"],
        )
        db.session.commit()
        steps.append({"step": 7, "action": "ingest_analyzer_result", "status": prelim["status"], "label": "SIMULATED"})

        item = promote_preliminary_to_result(
            prelim["result_id"],
            organization_id=org,
            order_id=order.id,
            actor="tech@pilot",
        )
        validate_result_item(item["id"], organization_id=org, actor="tech@pilot")
        order.status = ORDER_PENDING_REVIEW
        result_row = BizResult.query.filter_by(order_id=order.id).first()
        if result_row:
            result_row.status = RESULT_PENDING_REVIEW
        db.session.commit()
        steps.append({"step": 9, "action": "technician_validate", "item_id": item["id"]})

        ensure_clinical_report(order)
        approve_report(order.order_code, doctor_note="SIMULATED approval", actor="doc@pilot")
        db.session.commit()
        steps.append({"step": 11, "action": "doctor_approve"})

        release = release_report_governed(order.order_code, organization_id=org, actor="doc@pilot")
        db.session.commit()
        steps.append({"step": 13, "action": "release_report", "verification_token": release.get("verification_token")})

        report = ClinicalReport.query.filter_by(order_id=order.id).first()
        steps.append({"step": 15, "action": "verify_ready", "report_status": report.report_status if report else None})

        print(json.dumps({"status": "SIMULATED", "steps": steps}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
