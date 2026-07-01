#!/usr/bin/env python3
"""Release candidate verification and artifact generation."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from scripts.go_live_rc1_lib import GENERATED_DIR, run_full_rc1_validation


CHECKS = []


def check(name, ok):
    CHECKS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'}: {name}")
    return ok


def main():
    print("\n=== DXCON RELEASE CANDIDATE VERIFY ===\n")
    result = run_full_rc1_validation(write_reports=True)

    check("e2e workflows", result["workflows"]["ok"])
    check("security checks", result["security"]["ok"])
    check("deployment checks", result["deployment"]["ok"])
    check("data integrity", result["integrity"]["ok"])
    check("performance smoke", result["performance"]["ok"])
    check("rc1 score", result["score"]["ready_for_rc1"])

    artifacts = [
        "RC1_REPORT.json",
        "RC1_CHECKLIST.json",
        "API_ROUTE_SUMMARY.json",
        "GO_LIVE_RISKS.json",
    ]
    artifacts_ok = all((GENERATED_DIR / name).exists() for name in artifacts)
    check("release artifacts", artifacts_ok)

    failed = [name for name, ok in CHECKS if not ok]
    print("\nSUMMARY:", len(CHECKS) - len(failed), "passed,", len(failed), "failed")
    print("SCORE:", json.dumps(result["score"], indent=2))
    if failed:
        print("FAILED:", failed)
        sys.exit(1)
    print("RELEASE CANDIDATE VERIFY PASSED\n")


if __name__ == "__main__":
    main()
