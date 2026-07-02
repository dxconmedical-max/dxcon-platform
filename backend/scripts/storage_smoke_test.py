#!/usr/bin/env python3
"""Storage operations smoke test."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.storage_stack_lib import run_storage_smoke


def main():
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.extensions.db import db

    print("\n=== DXCON STORAGE SMOKE TEST ===\n")
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        result = run_storage_smoke(app)
    for name, ok in result["steps"].items():
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
    print(f"\nSmoke: {result['passed']}/{result['total']}")
    if not result["ok"]:
        sys.exit(1)
    print("STORAGE SMOKE TEST PASSED\n")


if __name__ == "__main__":
    main()
