#!/usr/bin/env python3
"""Verify UAT tenant and dataset readiness."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.extensions.db import db
from scripts.uat_tenant_lib import reseed_staging_data, verify_uat_data


def main():
    print("\n=== DXCON UAT DATA VERIFY ===\n")
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        reseed_staging_data()
        result = verify_uat_data(app)
    for name, payload in result["checks"].items():
        print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {name}")
    print(f"\nSUMMARY: {result['passed']}/{result['total']} passed")
    if not result["ok"]:
        sys.exit(1)
    print("UAT DATA VERIFY PASSED\n")


if __name__ == "__main__":
    main()
