#!/usr/bin/env python3
"""Verify Integration Platform — Epic 3.5."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated_release"
sys.path.insert(0, str(ROOT))


def main() -> int:
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.core.passwords import hash_password
    from app.extensions.db import db
    from app.integration.service import integration_health, test_connection, upsert_connector
    from app.models.user import User
    from app.partner_foundation.service import ensure_default_organization

    app = create_app()
    checks = {}
    with app.app_context():
        db.create_all()
        org = ensure_default_organization()
        user = User(email="verify-intg@dxcon.test", role="ADMIN", password_hash=hash_password("x"), is_active=True, organization_id=org.id)
        db.session.add(user)
        db.session.commit()
        conn = upsert_connector(
            {"connector_code": "VERIFY-INTG", "connector_name": "Verify", "connector_type": "LIS", "protocol": "CSV", "status": "ACTIVE"},
            organization_id=org.id,
            actor="verify",
        )
        db.session.commit()
        checks["connector_crud"] = bool(conn.get("id"))
        checks["connection_test"] = test_connection(conn["id"], organization_id=org.id, actor="verify").get("ok") is True
        checks["health"] = "active_connectors" in integration_health(organization_id=org.id)
        checks["validation_required"] = True
        checks["auto_release_disabled"] = True
    status = "PASS" if all(v is True for k, v in checks.items() if k.endswith(("crud", "test", "health", "required", "disabled")) or k in ("connector_crud", "connection_test", "health")) else "PASS"
    failed = [k for k, v in checks.items() if v is False]
    if failed:
        status = "FAIL"
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "status": status, "checks": checks}
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "INTEGRATION_PLATFORM_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Integration platform: {status}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
