#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.enterprise_master_lib import print_verify_banner
from scripts.production_staging_lib import run_phase_b_runtime_infrastructure, run_phase_gate


def main():
    result = run_phase_gate("B", run_phase_b_runtime_infrastructure)
    score = result.get("phase_report", {}).get("infrastructure_score", 0)
    print_verify_banner("DXCON PRODUCTION STAGING PHASE B - RUNTIME INFRASTRUCTURE", result.get("sections", {}))
    print(f"Infrastructure Score: {score}")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
