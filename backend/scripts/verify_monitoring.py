#!/usr/bin/env python3
"""Epic 8 — Monitoring stack verification."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from production_readiness_lib import finding, score_findings, utc_now, write_report  # noqa: E402


def main() -> int:
    findings = []
    prom = REPO / "deployment" / "monitoring" / "prometheus.yml"
    grafana = REPO / "deployment" / "monitoring" / "grafana"
    alerts = REPO / "deployment" / "monitoring" / "alerts" / "dxcon-alerts.yml"
    findings.append(finding("PASS" if prom.exists() else "WARNING", "prometheus_config"))
    findings.append(finding("PASS" if grafana.exists() else "WARNING", "grafana_dashboards"))
    findings.append(finding("PASS" if alerts.exists() else "WARNING", "alert_rules"))

    verify_stack = ROOT / "scripts" / "verify_monitoring_stack.py"
    if verify_stack.exists():
        proc = subprocess.run([sys.executable, str(verify_stack)], capture_output=True, text=True)
        findings.append(
            finding("PASS" if proc.returncode == 0 else "WARNING", "monitoring_stack_script", proc.stdout[-200:])
        )

    from app import create_app

    app = create_app()
    with app.app_context():
        client = app.test_client()
        health = client.get("/api/v1/system/health")
        findings.append(finding("PASS" if health.status_code == 200 else "FAIL", "system_health_endpoint"))
        obs = client.get("/api/v1/observability/health")
        findings.append(
            finding(
                "PASS" if obs.status_code in (200, 404) else "WARNING",
                "observability_health",
                f"status={obs.status_code}",
            )
        )

    scored = score_findings(findings)
    status = "PASS" if scored["counts"].get("FAIL", 0) == 0 else "FAIL"
    report = {"generated_at": utc_now(), "status": status, "findings": findings, "score": scored}
    path = write_report("MONITORING_EPIC8_REPORT.json", report)
    print(f"\n=== DXCON MONITORING VERIFY ===\nStatus: {status}\nReport: {path}\n")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
