#!/usr/bin/env python3
"""Bootstrap UAT staging tenant and core actors."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.extensions.db import db
from scripts.uat_tenant_lib import bootstrap_tenant


def main():
    print("\n=== DXCON UAT TENANT BOOTSTRAP ===\n")
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        result = bootstrap_tenant()
    for key, value in result.items():
        print(f"{key}: {value}")
    print("\nUAT TENANT BOOTSTRAP COMPLETE\n")


if __name__ == "__main__":
    main()
