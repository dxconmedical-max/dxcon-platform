#!/usr/bin/env python3
"""Verify collector assignment scope — Epic 7."""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated_release"


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from app import create_app
    from app.extensions.db import db
    from app.models.driver import Driver
    from app.models.user import User
    from flask_jwt_extended import create_access_token

    app = create_app()
    with app.app_context():
        db.create_all()
        patient = User(id=str(uuid.uuid4()), email="pat@test.com", role="PATIENT", password_hash="x")
        collector = Driver(id=str(uuid.uuid4()), driver_code="C1", full_name="C")
        other = Driver(id=str(uuid.uuid4()), driver_code="C2", full_name="O")
        db.session.add_all([patient, collector, other])
        db.session.commit()
        token = create_access_token(identity=patient.id, additional_claims={"role": "PATIENT"})
        client = app.test_client()
        denied = client.get(
            f"/api/v1/mobile/collector/jobs?collector_id={collector.id}",
            headers={"Authorization": f"Bearer {token}"},
        ).status_code
        checks = {"collector_scope_denied_for_patient": denied == 403}
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
    }
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "COLLECTOR_ASSIGNMENT_SCOPE_REPORT.json").write_text(json.dumps(report, indent=2))
    print(f"Collector assignment scope: {report['status']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
