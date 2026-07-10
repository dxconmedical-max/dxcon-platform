#!/usr/bin/env python3
"""Verify connector registry — Epic 3.5."""
import json, os, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
GENERATED = ROOT / "generated_release"

def main():
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.extensions.db import db
    from app.integration.service import list_connectors, upsert_connector
    from app.partner_foundation.service import ensure_default_organization
    app = create_app()
    with app.app_context():
        db.create_all()
        org = ensure_default_organization().id
        upsert_connector({"connector_code": "REG-1", "connector_name": "R", "connector_type": "LIS", "protocol": "CSV"}, organization_id=org, actor="v")
        db.session.commit()
        ok = list_connectors(organization_id=org)["pagination"]["total"] >= 1
    report = {"status": "PASS" if ok else "FAIL", "registry": ok, "generated_at": datetime.now(timezone.utc).isoformat()}
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "CONNECTOR_REGISTRY_REPORT.json").write_text(json.dumps(report, indent=2))
    print(report["status"])
    return 0 if ok else 1
if __name__ == "__main__":
    raise SystemExit(main())
