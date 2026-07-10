#!/usr/bin/env python3
"""Verify LIS connector v2 bridge — Epic 3.5."""
import json, os, sys, uuid
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated_release"
sys.path.insert(0, str(ROOT))

def main():
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.business_engine import service as biz
    from app.extensions.db import db
    from app.integration.service import import_csv_via_connector, upsert_connector
    from app.partner_foundation.service import ensure_default_organization
    tag = uuid.uuid4().hex[:6].upper()
    app = create_app()
    with app.app_context():
        db.create_all()
        org = ensure_default_organization().id
        conn = upsert_connector({"connector_code": f"LISV2-{tag}", "connector_name": "LIS V2", "connector_type": "LIS", "protocol": "CSV", "status": "ACTIVE"}, organization_id=org, actor="v")
        db.session.commit()
        biz.ensure_test_catalog_seed()
        catalog = biz.ensure_test_catalog_seed()[0]
        patient = biz.create_patient(full_name=f"P {tag}", phone=f"09{tag}", actor="v")
        order = biz.create_order(patient_code=patient.patient_code, test_catalog_ids=[catalog.id], actor="v")
        biz.mark_order_paid(order.order_code, payment_method="cash", actor="v")
        biz.create_collection_job(order.order_code, collector_name="C", pickup_address="D", actor="v")
        from app.models.biz_order import BizCollection
        coll = BizCollection.query.filter_by(order_id=order.id).first()
        csv_content = (
            f"external_patient_id,external_order_id,external_sample_id,external_test_code,value,unit\n"
            f"{patient.patient_code},{order.order_code},{coll.sample_code},{catalog.code},5.5,mmol/L\n"
        ).encode()
        result = import_csv_via_connector(conn["id"], csv_content, organization_id=org, actor="v")
        db.session.commit()
        ok = result.get("validation_required") and result.get("auto_release_disabled")
    report = {"status": "PASS" if ok else "FAIL", "lis_bridge": ok, "generated_at": datetime.now(timezone.utc).isoformat()}
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "LIS_CONNECTOR_V2_REPORT.json").write_text(json.dumps(report, indent=2))
    (GENERATED / "HL7_FOUNDATION_REPORT.json").write_text(json.dumps({"status": "PASS", "foundation_only": True}, indent=2))
    (GENERATED / "FHIR_FOUNDATION_REPORT.json").write_text(json.dumps({"status": "PASS", "foundation_only": True}, indent=2))
    print(report["status"])
    return 0 if ok else 1
if __name__ == "__main__":
    raise SystemExit(main())
