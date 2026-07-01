#!/usr/bin/env python3
"""Seed UAT staging dataset."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.extensions.db import db
from scripts.uat_tenant_lib import seed_uat_data


def main():
    print("\n=== DXCON UAT DATA SEED ===\n")
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        result = seed_uat_data()
    for key, value in result.items():
        print(f"{key}: {value}")
    print("\nUAT DATA SEED COMPLETE\n")


if __name__ == "__main__":
    main()
