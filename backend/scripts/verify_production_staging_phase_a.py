#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.enterprise_master_lib import print_verify_banner
from scripts.production_staging_lib import run_phase_a_production_config, run_phase_gate


def main():
    result = run_phase_gate("A", run_phase_a_production_config)
    score = result.get("phase_report", {}).get("production_config_score", 0)
    print_verify_banner("DXCON PRODUCTION STAGING PHASE A - PRODUCTION CONFIGURATION", result.get("sections", {}))
    print(f"Production Config Score: {score}")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
