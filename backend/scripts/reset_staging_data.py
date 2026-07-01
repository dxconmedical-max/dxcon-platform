#!/usr/bin/env python3
"""Reset or reseed UAT staging data."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.extensions.db import db
from scripts.uat_tenant_lib import reseed_staging_data, reset_staging_data


def main():
    parser = argparse.ArgumentParser(description="Reset UAT staging data")
    parser.add_argument("--reseed", action="store_true", help="Reset then seed UAT dataset")
    args = parser.parse_args()

    print("\n=== DXCON UAT STAGING RESET ===\n")
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        if args.reseed:
            result = reseed_staging_data()
            print("mode: reseed")
        else:
            result = reset_staging_data()
            print("mode: reset")
    for key, value in result.items():
        print(f"{key}: {value}")
    print("\nUAT STAGING RESET COMPLETE\n")


if __name__ == "__main__":
    main()
