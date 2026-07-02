#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.enterprise_signoff_lib import run_enterprise_signoff

def main():
    result = run_enterprise_signoff()
    print("\n=== DXCON ENTERPRISE PACK 10 - ENTERPRISE SIGNOFF ===\n")
    print(f"Decision: {result.get('decision')}")
    print(f"Go-Live Score: {result.get('go_live_score')}")
    for name, score in (result.get("scores") or {}).items():
        print(f"{name.title()} Score: {score}")
    print(f"\n{'PASS' if result.get('ok') else 'FAIL'}: enterprise_signoff\n")
    return 0 if result.get("ok") else 1

if __name__ == "__main__":
    raise SystemExit(main())
