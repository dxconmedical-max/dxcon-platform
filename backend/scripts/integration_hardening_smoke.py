#!/usr/bin/env python3
"""Integration hardening smoke test."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from integration_hardening_lib import run_integration_hardening_smoke


def main() -> int:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.extensions.db import db

    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        result = run_integration_hardening_smoke(app)

    steps = result.get("steps", {})
    print("\n=== DXCON INTEGRATION HARDENING SMOKE TEST ===\n")
    for name, ok in steps.items():
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
    print(f"\nSmoke: {result.get('passed')}/{result.get('total')}")
    if result.get("ok"):
        print("INTEGRATION HARDENING SMOKE TEST PASSED\n")
        return 0
    print("INTEGRATION HARDENING SMOKE TEST FAILED\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
