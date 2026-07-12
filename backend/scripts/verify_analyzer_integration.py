#!/usr/bin/env python3
"""Verify Release 7.0 Sprint 5 — Analyzer Integration Foundation."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))

import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

ROUTES = (
    "/api/v1/analyzers",
    "/api/v1/integrations/analyzer/messages",
    "/api/v1/integrations/analyzer/quarantine",
    "/api/v1/integrations/analyzer/test-mappings",
    "/api/v1/integrations/analyzer/results",
    "/api/v1/lab/analyzer-dashboard",
    "/api/v1/lab/result-review",
)

FRONTEND = {
    "analyzer_dashboard": REPO / "apps/web/src/app/app/lab/analyzers/page.tsx",
    "result_review": REPO / "apps/web/src/app/app/lab/results-review/page.tsx",
    "quarantine": REPO / "apps/web/src/app/app/lab/quarantine/page.tsx",
    "analyzer_api": REPO / "apps/web/src/lib/api/analyzer.ts",
}

REPORTS = {
    "ANALYZER_PLATFORM_REPORT.json": ROOT / "generated_release" / "ANALYZER_PLATFORM_REPORT.json",
    "ANALYZER_SECURITY_REPORT.json": ROOT / "generated_release" / "ANALYZER_SECURITY_REPORT.json",
    "RESULT_INGESTION_REPORT.json": ROOT / "generated_release" / "RESULT_INGESTION_REPORT.json",
    "ANALYZER_QC_REPORT.json": ROOT / "generated_release" / "ANALYZER_QC_REPORT.json",
    "ANALYZER_UI_REPORT.json": REPO / "apps" / "web" / "generated-release" / "ANALYZER_UI_REPORT.json",
}


def main() -> int:
    from app import create_app

    app = create_app()
    rules = {r.rule for r in app.url_map.iter_rules()}
    route_ok = {r: r in rules for r in ROUTES}
    frontend_ok = {k: v.exists() for k, v in FRONTEND.items()}

    proc = subprocess.run([sys.executable, "-m", "unittest", "tests.test_analyzer_integration", "-q"], cwd=ROOT)
    tests_ok = proc.returncode == 0

    service = (ROOT / "app/analyzer_integration/service.py").read_text()
    security = {
        "no_auto_release": "auto_released=False" in service,
        "original_preserved": "original_value" in service,
        "quarantine_workflow": "IntegrationQuarantine" in service,
        "tenant_isolation": "organization_id" in service,
        "simulator_guard": "Simulator disabled" in (ROOT / "app/analyzer_integration/adapters.py").read_text(),
    }
    ingestion = {
        "duplicate_detection": "DUPLICATE_RESULT" in service,
        "unmapped_quarantine": "UNMAPPED_TEST" in service,
        "unit_mismatch": "UNIT_MISMATCH" in service,
        "preliminary_only": "PENDING_REVIEW" in service,
    }

    platform = {
        "migration": (ROOT / "migrations/018_analyzer_integration.sql").exists(),
        "routes": all(route_ok.values()),
        "tests": tests_ok,
        "frontend": all(frontend_ok.values()),
        "adapter_framework": (ROOT / "app/analyzer_integration/adapters.py").exists(),
    }

    failed = [k for k, v in {**platform, **security, **ingestion}.items() if not v]
    status = "PASS" if not failed else "FAIL"
    ts = datetime.now(timezone.utc).isoformat()

    payloads = {
        "ANALYZER_PLATFORM_REPORT.json": {"release": "7.0", "sprint": "Sprint 5", "status": status, "checks": platform, "routes": route_ok, "generated_at": ts},
        "ANALYZER_SECURITY_REPORT.json": {"release": "7.0", "sprint": "Sprint 5", "status": status, "checks": security, "generated_at": ts},
        "RESULT_INGESTION_REPORT.json": {"release": "7.0", "sprint": "Sprint 5", "status": status, "checks": ingestion, "generated_at": ts},
        "ANALYZER_QC_REPORT.json": {"release": "7.0", "sprint": "Sprint 5", "status": status, "note": "QC rule-engine interfaces foundation; Westgard not claimed", "generated_at": ts},
        "ANALYZER_UI_REPORT.json": {"release": "7.0", "sprint": "Sprint 5", "status": status, "pages": frontend_ok, "generated_at": ts},
    }

    for name, path in REPORTS.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payloads[name], indent=2), encoding="utf-8")

    print(f"Analyzer Integration verification: {status}")
    if failed:
        print("Failed:", failed)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
