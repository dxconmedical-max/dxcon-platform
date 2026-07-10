#!/usr/bin/env python3
"""Release 3.0 Epic 9 — AI Platform Core verification."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_platform_lib import run_ai_platform_verification
from production_readiness_lib import utc_now, write_report


def main() -> int:
    result = run_ai_platform_verification()
    checks = result.get("checks", {})
    gates = {
        "ai_gateway": checks.get("ai_platform_smoke", {}).get("ok", False),
        "ai_governance": checks.get("ai_platform_smoke", {}).get("steps", {}).get("governance_list", False),
        "prompt_registry": checks.get("prompt_versioning", {}).get("ok", False),
        "phi_protection": checks.get("phi_redaction", {}).get("ok", False),
        "ai_audit": checks.get("ai_platform_smoke", {}).get("steps", {}).get("audit_written", False),
        "ai_sdk": checks.get("ai_platform_smoke", {}).get("steps", {}).get("sdk_manifest", False),
        "memory": checks.get("ai_platform_smoke", {}).get("steps", {}).get("memory_session", False),
        "rag": checks.get("ai_platform_smoke", {}).get("steps", {}).get("rag_retrieve", False),
    }
    status = "PASS" if result.get("ok") and all(gates.values()) else "FAIL"
    report = {
        "generated_at": utc_now(),
        "status": status,
        "release": "3.0",
        "epic": 9,
        "gates": gates,
        "verification": result,
    }
    path = write_report("AI_PLATFORM_CORE_EPIC9_REPORT.json", report)
    print("\n=== EPIC 9 AI PLATFORM CORE ===\n")
    for name, ok in gates.items():
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
    print(f"\nOverall: {status}")
    print(f"Report: {path}\n")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
