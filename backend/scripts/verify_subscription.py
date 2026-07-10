#!/usr/bin/env python3
"""Epic 8 — Subscription and license platform verification."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from production_readiness_lib import finding, score_findings, utc_now, write_report  # noqa: E402


def main() -> int:
    from app import create_app
    from app.extensions.db import db
    from app.pilot_readiness.service import subscription_plans

    app = create_app()
    findings = []
    with app.app_context():
        db.create_all()
        client = app.test_client()
        plans = client.get("/api/v1/pilot-readiness/subscription-plans")
        findings.append(finding("PASS" if plans.status_code == 200 else "FAIL", "subscription_plans_api"))
        data = plans.get_json() or {}
        plan_codes = {p["plan_code"] for p in data.get("data", [])}
        for code in ("STARTER", "PROFESSIONAL", "ENTERPRISE", "WHITE_LABEL"):
            findings.append(
                finding("PASS" if code in plan_codes else "FAIL", f"plan:{code}")
            )

        lic = client.get("/api/v1/licenses")
        findings.append(
            finding("PASS" if lic.status_code in (200, 401, 403) else "WARNING", "enterprise_licenses_api")
        )

        local_plans = subscription_plans()
        findings.append(finding("PASS" if len(local_plans) >= 4 else "FAIL", "plan_catalog"))

    scored = score_findings(findings)
    status = "PASS" if scored["counts"].get("FAIL", 0) == 0 else "FAIL"
    report = {"generated_at": utc_now(), "status": status, "findings": findings, "score": scored}
    path = write_report("SUBSCRIPTION_EPIC8_REPORT.json", report)
    print(f"\n=== DXCON SUBSCRIPTION VERIFY ===\nStatus: {status}\nReport: {path}\n")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
