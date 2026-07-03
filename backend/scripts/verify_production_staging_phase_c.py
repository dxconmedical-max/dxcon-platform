#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.enterprise_master_lib import print_verify_banner
from scripts.production_staging_lib import run_phase_c_observability_operations, run_phase_gate


def main():
    result = run_phase_gate("C", run_phase_c_observability_operations)
    score = result.get("phase_report", {}).get("observability_score", 0)
    print_verify_banner("DXCON PRODUCTION STAGING PHASE C - OBSERVABILITY OPERATIONS", result.get("sections", {}))
    print(f"Observability Score: {score}")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
