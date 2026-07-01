#!/usr/bin/env python3
"""PostgreSQL staging/production readiness validation."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.extensions.db import db
from app.infrastructure.production_readiness import database_dialect_report, validate_database


def main():
    print("\n=== DXCON POSTGRESQL READINESS ===\n")
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        dev_report = database_dialect_report(app)
        print("dev report:", json.dumps(dev_report, indent=2))

    staging_app = create_app()
    staging_app.config.update(
        {
            "TESTING": False,
            "APP_ENV": "staging",
            "SQLALCHEMY_DATABASE_URI": "postgresql://dxcon:dxcon@localhost:5432/dxcon_staging",
            "CORS_ORIGINS": "https://staging.dxcon.test",
            "REDIS_URL": "redis://localhost:6379/0",
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": 587,
            "SMTP_FROM": "noreply@staging.dxcon.test",
        }
    )
    report = database_dialect_report(staging_app)
    print("staging report:", json.dumps(report, indent=2))
    try:
        validate_database(staging_app)
        print("OK: staging PostgreSQL validation")
    except Exception as exc:
        print("FAIL:", exc)
        sys.exit(1)

    sqlite_app = create_app()
    sqlite_app.config.update({"TESTING": False, "APP_ENV": "staging", "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    try:
        validate_database(sqlite_app)
        print("FAIL: sqlite should be blocked in staging")
        sys.exit(1)
    except RuntimeError:
        print("OK: sqlite blocked in staging")

    print("\nPOSTGRESQL READINESS PASSED\n")


if __name__ == "__main__":
    main()
