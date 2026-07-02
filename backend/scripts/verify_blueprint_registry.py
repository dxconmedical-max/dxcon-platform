#!/usr/bin/env python3
"""Verify Flask blueprint registration and route inventory."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from blueprint_registry_lib import run_blueprint_registry_verification


def verify_no_import_cycles() -> dict:
    proc = subprocess.run(
        [sys.executable, "-c", "from app import create_app; create_app()"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "stderr_tail": proc.stderr.splitlines()[-5:],
    }


def main() -> int:
    print("\n=== DXCON BLUEPRINT REGISTRY VERIFY ===\n")
    import_cycles = verify_no_import_cycles()
    print(f"{'PASS' if import_cycles.get('ok') else 'FAIL'}: import_cycles")
    if not import_cycles.get("ok"):
        for line in import_cycles.get("stderr_tail", []):
            print(f"  {line}")

    result = run_blueprint_registry_verification()
    for name, payload in result.get("checks", {}).items():
        print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {name}")
        if not payload.get("ok"):
            for key, value in payload.items():
                if key != "ok":
                    print(f"  {key}: {value}")

    ok = import_cycles.get("ok") and result.get("ok")
    print(f"\nSUMMARY: {result.get('passed')}/{result.get('total')} checks")
    if ok:
        print("BLUEPRINT REGISTRY VERIFY PASSED\n")
        return 0
    print("BLUEPRINT REGISTRY VERIFY FAILED\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
