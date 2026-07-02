#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.code_quality_excellence_lib import run_code_quality_excellence_verification
from scripts.enterprise_master_lib import print_verify_banner

def main():
    result = run_code_quality_excellence_verification()
    print_verify_banner("DXCON ENTERPRISE PACK 8 - CODE QUALITY", result.get("sections", {}))
    return 0 if result.get("ok") else 1

if __name__ == "__main__":
    raise SystemExit(main())
