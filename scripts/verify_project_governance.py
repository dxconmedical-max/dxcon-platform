#!/usr/bin/env python3
"""Verify DxCon Project Governance Pack — required docs and sections."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
SPRINTS = DOCS / "sprints"
GENERATED = REPO / "backend" / "generated_release"

REQUIRED_FILES = (
    DOCS / "PROJECT_MANUAL.md",
    DOCS / "PRODUCT_BACKLOG.md",
    DOCS / "RELEASE_PLAN.md",
    DOCS / "LAUNCH_CHECKLIST.md",
    DOCS / "SPRINT_TEMPLATE.md",
    SPRINTS / "SPRINT-001-MDM.md",
    SPRINTS / "SPRINT-002-LAUNCH-UI.md",
    SPRINTS / "SPRINT-003-BUSINESS-STABILIZATION.md",
)

SECTION_CHECKS: dict[Path, tuple[str, ...]] = {
    DOCS / "PROJECT_MANUAL.md": (
        "Project Mission",
        "Current Operating Model",
        "Coding Rules",
        "API Rules",
        "Database Migration Rules",
        "Testing Rules",
        "Release Rules",
        "Rollback Rules",
        "Bug Handling Rules",
        "Production Deployment Rules",
        "Security Baseline",
        "Audit Baseline",
    ),
    DOCS / "PRODUCT_BACKLOG.md": (
        "Patient Management",
        "Order Management",
        "Master Data Management",
        "Commercial Launch",
        "TODO",
        "IN_PROGRESS",
        "DONE",
        "Critical",
    ),
    DOCS / "RELEASE_PLAN.md": (
        "Release 1.0",
        "Release 1.1",
        "Release 1.2",
        "Release 2.0",
        "Release 3.0",
    ),
    DOCS / "LAUNCH_CHECKLIST.md": (
        "Domain",
        "DNS",
        "SSL",
        "Email",
        "Master Data",
        "Real Users",
        "UAT",
        "Backup",
        "Monitoring",
        "Security",
        "Pilot",
        "Go Live",
    ),
    DOCS / "SPRINT_TEMPLATE.md": (
        "Goal",
        "Business value",
        "Scope",
        "Out of scope",
        "Deliverables",
        "Data impact",
        "API impact",
        "UI impact",
        "Tests",
        "Verification",
        "Definition of Done",
        "Commit message",
    ),
    SPRINTS / "SPRINT-001-MDM.md": ("Master Data Management", "Definition of Done"),
    SPRINTS / "SPRINT-002-LAUNCH-UI.md": ("Launch UI", "Definition of Done"),
    SPRINTS / "SPRINT-003-BUSINESS-STABILIZATION.md": (
        "Business",
        "Definition of Done",
    ),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def check_file(path: Path) -> dict:
    rel = str(path.relative_to(REPO))
    result: dict = {"path": rel, "exists": path.exists(), "ok": False, "missing_sections": []}
    if not path.exists():
        return result
    text = path.read_text(encoding="utf-8")
    text_lower = text.lower()
    required = SECTION_CHECKS.get(path, ())
    missing = [s for s in required if s.lower() not in text_lower]
    result["missing_sections"] = missing
    result["ok"] = len(missing) == 0
    return result


def main() -> int:
    print("\n=== DXCON PROJECT GOVERNANCE VERIFY ===\n")
    checks = [check_file(p) for p in REQUIRED_FILES]
    passed = sum(1 for c in checks if c["ok"])
    total = len(checks)
    ok = passed == total

    for c in checks:
        status = "PASS" if c["ok"] else "FAIL"
        print(f"  [{status}] {c['path']}")
        if c["missing_sections"]:
            for section in c["missing_sections"]:
                print(f"         missing section: {section}")
        if not c["exists"]:
            print("         file not found")

    report = {
        "generated_at": utc_now(),
        "ok": ok,
        "passed": passed,
        "total": total,
        "checks": checks,
    }
    GENERATED.mkdir(parents=True, exist_ok=True)
    report_path = GENERATED / "PROJECT_GOVERNANCE_REPORT.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nChecks passed: {passed}/{total}")
    print(f"Report: {report_path}")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
