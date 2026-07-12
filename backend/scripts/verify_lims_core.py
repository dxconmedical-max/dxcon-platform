#!/usr/bin/env python3
"""Verify Release 7.0 LIMS Core artifacts."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "generated_release" / "LIMS_CORE_REPORT.json"

CHECKS = {
    "models": ROOT / "app/models/lims_core.py",
    "service": ROOT / "app/lims_core/service.py",
    "routes": ROOT / "app/api/lims_core/routes.py",
    "migration": ROOT / "migrations/016_lims_core.sql",
    "tests": ROOT / "tests/test_lims_core.py",
    "statuses": ROOT / "app/core/statuses.py",
}

FRONTEND = {
    "specimens_page": ROOT.parent / "apps/web/src/app/app/lab/specimens/page.tsx",
    "barcode_page": ROOT.parent / "apps/web/src/app/app/lab/barcode/page.tsx",
    "accession_page": ROOT.parent / "apps/web/src/app/app/lab/accession/page.tsx",
    "timeline_page": ROOT.parent / "apps/web/src/app/app/lab/timeline/page.tsx",
    "lab_api": ROOT.parent / "apps/web/src/lib/api/lab.ts",
}

DOCS = ROOT.parent / "docs/sprints/RELEASE-7.0-LIMS-CORE.md"


def main() -> int:
    results = {name: path.exists() for name, path in CHECKS.items()}
    frontend = {name: path.exists() for name, path in FRONTEND.items()}
    results["docs"] = DOCS.exists()
    results["frontend"] = all(frontend.values())

    service_text = CHECKS["service"].read_text(encoding="utf-8") if CHECKS["service"].exists() else ""
    results["barcode_pattern"] = "DX" in service_text and "next_human_readable_barcode" in service_text
    results["lifecycle_transitions"] = "LIMS_SPECIMEN_TRANSITIONS" in (CHECKS["statuses"].read_text(encoding="utf-8") if CHECKS["statuses"].exists() else "")
    results["dashboard_kpis"] = "samples_today" in service_text and "released_today" in service_text

    failed = [k for k, v in results.items() if not v]
    status = "PASS" if not failed else "FAIL"

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "release": "7.0",
        "sprint": "Sprint 3 — LIMS Core",
        "status": status,
        "checks": results,
        "frontend_checks": frontend,
        "failed": failed,
        "api_endpoints": [
            "GET/POST /api/v1/specimens",
            "GET/PUT /api/v1/specimens/{id}",
            "POST /api/v1/specimens/{id}/transition",
            "GET /api/v1/specimens/{id}/timeline",
            "GET/POST /api/v1/barcodes",
            "GET/POST /api/v1/accessions",
            "GET /api/v1/accessions/{id}",
            "GET /api/v1/lab/dashboard",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"LIMS Core verification: {status}")
    if failed:
        print("Failed:", failed)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
