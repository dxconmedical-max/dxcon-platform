#!/usr/bin/env python3
"""RC2 production cutover validation with full regression."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.go_live_rc2_lib import GENERATED_DIR, run_rc2_validation


def main():
    print("\n=== DXCON RC2 CUTOVER VALIDATION ===\n")
    result = run_rc2_validation(write_reports=True, run_regression=True)
    print("Regression:", result["regression"]["passed"], "/", result["regression"]["total"])
    print("Cutover:", result["cutover"]["passed"], "/", result["cutover"]["total"])
    print("Smoke:", result["smoke"]["passed"], "/", result["smoke"]["total"])
    print("Score:", json.dumps(result["score"], indent=2))
    artifacts = [
        "RC2_REPORT.json",
        "PRODUCTION_CUTOVER_CHECKLIST.json",
        "ROLLBACK_CHECKLIST.json",
        "ENVIRONMENT_MATRIX.json",
        "ROLLBACK_PACKAGE.json",
    ]
    missing = [name for name in artifacts if not (GENERATED_DIR / name).exists()]
    if missing:
        print("FAIL: missing artifacts", missing)
        sys.exit(1)
    if not result["ok"]:
        failed_domains = [
            name for name, payload in result["regression"]["domains"].items() if not payload.get("ok")
        ]
        if failed_domains:
            print("FAILED regression domains:", failed_domains)
        sys.exit(1)
    print("\nRC2 CUTOVER VALIDATION PASSED\n")


if __name__ == "__main__":
    main()
