#!/usr/bin/env python3
"""Validate production/staging environment templates and config rules."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.core.config_validation import validate_config
from app.infrastructure.production_readiness import database_dialect_report, evaluate_go_live_blockers


def _load_env_example(name):
    path = ROOT / name
    if not path.exists():
        return None
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def main():
    print("\n=== DXCON PRODUCTION ENV CHECK ===\n")
    errors = 0

    for name in (".env.staging.example", ".env.production.example"):
        if (ROOT / name).exists():
            print("OK:", name, "present")
        else:
            print("FAIL: missing", name)
            errors += 1

    staging_values = _load_env_example(".env.staging.example") or {}
    production_values = _load_env_example(".env.production.example") or {}

    for label, values in (("staging", staging_values), ("production", production_values)):
        cors = values.get("CORS_ORIGINS", "")
        db_url = values.get("DATABASE_URL", "")
        if cors and cors != "*":
            print(f"OK: {label} explicit CORS")
        else:
            print(f"FAIL: {label} CORS must be explicit")
            errors += 1
        if db_url.startswith("postgresql"):
            print(f"OK: {label} PostgreSQL DATABASE_URL")
        else:
            print(f"FAIL: {label} must use PostgreSQL")
            errors += 1
        if values.get("REDIS_URL"):
            print(f"OK: {label} REDIS_URL set")
        else:
            print(f"FAIL: {label} REDIS_URL missing")
            errors += 1
        if values.get("SMTP_HOST") and values.get("SMTP_FROM"):
            print(f"OK: {label} SMTP configured")
        else:
            print(f"FAIL: {label} SMTP incomplete")
            errors += 1

    staging_app = create_app()
    staging_app.config.update(
        {
            "TESTING": False,
            "APP_ENV": "staging",
            "CORS_ORIGINS": staging_values.get("CORS_ORIGINS", "https://staging.dxcon.test"),
            "SQLALCHEMY_DATABASE_URI": staging_values.get(
                "DATABASE_URL",
                "postgresql://dxcon:dxcon@postgres:5432/dxcon_staging",
            ),
            "REDIS_URL": staging_values.get("REDIS_URL", "redis://redis:6379/0"),
            "SMTP_HOST": staging_values.get("SMTP_HOST", "smtp.example.com"),
            "SMTP_PORT": int(staging_values.get("SMTP_PORT", "587")),
            "SMTP_FROM": staging_values.get("SMTP_FROM", "noreply@dxcon.test"),
            "SECRET_KEY": "staging-secret-key",
            "JWT_SECRET_KEY": "staging-jwt-secret-key",
        }
    )
    report = database_dialect_report(staging_app)
    if report["ok"] and report["dialect"] == "postgresql":
        print("OK: staging dialect report")
    else:
        print("FAIL: staging dialect report", report)
        errors += 1

    try:
        validate_config(staging_app)
        print("OK: staging validate_config")
    except Exception as exc:
        print("FAIL: staging validate_config", exc)
        errors += 1

    blockers = evaluate_go_live_blockers(staging_app)
    if blockers["ready"]:
        print("OK: staging go-live blockers cleared")
    else:
        print("WARN: staging blockers remain (redis/smtp connectivity expected locally)", blockers["blockers"])
        if any(item["id"] in {"cors_wildcard", "sqlite_database", "postgresql_required"} for item in blockers["blockers"]):
            errors += 1

    print("\nSUMMARY:", "PASS" if errors == 0 else f"{errors} failure(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
