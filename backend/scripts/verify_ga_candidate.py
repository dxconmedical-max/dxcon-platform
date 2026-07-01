#!/usr/bin/env python3
"""GA candidate validation — full regression, smoke, and readiness gates."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))

from scripts.ga_candidate_lib import GENERATED_DIR, run_ga_validation


def verify_release_isolation() -> dict:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "release_isolation.py"), "check", "--release", "staging-sprint-5"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout.splitlines()[-5:],
    }


def main():
    print("\n=== DXCON GA CANDIDATE VALIDATION ===\n")
    result = run_ga_validation(write_reports=True, run_regression=True, run_tests=True)
    isolation = verify_release_isolation()

    for name, payload in result["sections"].items():
        if name == "artifacts":
            print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {name}")
            for sub_name in ("rc2", "staging", "blockers"):
                sub = payload.get(sub_name, {})
                print(f"  {'PASS' if sub.get('ok') else 'FAIL'}: {sub_name}")
            continue
        if name == "smoke_suite":
            print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {name}")
            for suite_name, suite_payload in payload.get("suites", {}).items():
                print(f"  {'PASS' if suite_payload.get('ok') else 'FAIL'}: {suite_name}")
            continue
        print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {name}")

    print(f"{'PASS' if isolation.get('ok') else 'FAIL'}: release_isolation")
    print(f"\nGA score: {result['score']['score']} | Ready: {result['score']['ready_for_ga']}")
    print(json.dumps(result["score"]["breakdown"], indent=2))

    required = ["GA_REPORT.json", "GA_CHECKLIST.json", "API_FREEZE_REPORT.json"]
    missing = [name for name in required if not (GENERATED_DIR / name).exists()]
    if missing:
        print("FAIL: missing GA artifacts", missing)
        sys.exit(1)

    if not isolation["ok"]:
        print("FAIL: release isolation")
        sys.exit(1)

    if not result["ok"]:
        failed = [name for name, payload in result["sections"].items() if not payload.get("ok")]
        print("FAILED sections:", failed)
        sys.exit(1)

    print("\nGA CANDIDATE VALIDATION PASSED\n")


if __name__ == "__main__":
    main()
