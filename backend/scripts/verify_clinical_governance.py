#!/usr/bin/env python3
"""Verify Release 8.0 Sprint 6 — Clinical Workflow and Result Governance."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "generated_release"

CHECKS = {
    "workflow": ROOT / "app/clinical_governance/workflow.py",
    "service": ROOT / "app/clinical_governance/service.py",
    "routes": ROOT / "app/api/clinical_governance/routes.py",
    "models": ROOT / "app/models/clinical_governance.py",
    "migration": ROOT / "migrations/019_clinical_workflow.sql",
    "tests": ROOT / "tests/test_clinical_governance.py",
    "pilot_flow": ROOT / "scripts/run_clinical_pilot_flow.py",
    "statuses": ROOT / "app/core/statuses.py",
}

FRONTEND = {
    "lab_result_review": ROOT.parent / "apps/web/src/app/app/lab/result-review/page.tsx",
    "doctor_review": ROOT.parent / "apps/web/src/app/app/doctor/review/page.tsx",
    "patient_results": ROOT.parent / "apps/web/src/app/app/patient/results/page.tsx",
    "clinic_reports": ROOT.parent / "apps/web/src/app/app/clinic/reports/page.tsx",
    "verify_public": ROOT.parent / "apps/web/src/app/verify-report/[token]/page.tsx",
    "clinical_api": ROOT.parent / "apps/web/src/lib/api/clinical.ts",
}

DOCS = [
    ROOT.parent / "docs/CLINICAL_WORKFLOW_CURRENT_STATE.md",
    ROOT.parent / "docs/CLINICAL_RESULT_WORKFLOW.md",
    ROOT.parent / "docs/RESULT_REPORT_FORMAT.md",
    ROOT.parent / "docs/REPORT_VERIFICATION.md",
]


def _run_tests() -> bool:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "tests.test_clinical_governance", "-v"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def main() -> int:
    results = {name: path.exists() for name, path in CHECKS.items()}
    frontend = {name: path.exists() for name, path in FRONTEND.items()}
    docs_ok = all(p.exists() for p in DOCS)

    status_text = CHECKS["statuses"].read_text(encoding="utf-8") if CHECKS["statuses"].exists() else ""
    service_text = CHECKS["service"].read_text(encoding="utf-8") if CHECKS["service"].exists() else ""

    results["workflow_transitions"] = "CLINICAL_RESULT_TRANSITIONS" in status_text
    results["no_auto_release"] = "never automatic" in service_text or "Explicit release" in service_text
    results["verification_no_phi"] = "no PHI" in service_text
    results["frontend"] = all(frontend.values())
    results["docs"] = docs_ok
    results["unit_tests"] = _run_tests() if CHECKS["tests"].exists() else False

    failed = [k for k, v in results.items() if not v]
    status = "PASS" if not failed else "FAIL"

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "release": "8.0",
        "sprint": "Sprint 6 — Clinical Workflow and Result Governance",
        "status": status,
        "checks": results,
        "frontend_checks": frontend,
        "failed": failed,
        "api_endpoints": [
            "GET /api/v1/clinical/technician/queue",
            "GET /api/v1/clinical/technician/results/{id}",
            "POST /api/v1/clinical/technician/results/{id}/validate",
            "POST /api/v1/clinical/technician/results/{id}/reject",
            "POST /api/v1/clinical/technician/promote",
            "GET /api/v1/clinical/doctor/queue",
            "POST /api/v1/clinical/release/{order_ref}",
            "GET /api/v1/verify-report/{token}",
        ],
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "SPRINT_6_RESULT_GOVERNANCE_REPORT.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Clinical governance verification: {status}")
    if failed:
        print("Failed:", failed)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
