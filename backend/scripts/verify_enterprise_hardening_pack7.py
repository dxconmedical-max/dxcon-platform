#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.performance_excellence_lib import run_performance_excellence_verification
from scripts.enterprise_master_lib import print_verify_banner

def main():
    result = run_performance_excellence_verification()
    print_verify_banner("DXCON ENTERPRISE PACK 7 - PERFORMANCE EXCELLENCE", result.get("sections", {}))
    return 0 if result.get("ok") else 1

if __name__ == "__main__":
    raise SystemExit(main())
