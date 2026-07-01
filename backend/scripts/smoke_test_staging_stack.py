#!/usr/bin/env python3
"""Smoke test staging deployment configuration."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.staging_stack_lib import parse_env_file, run_staging_verification


def main():
    print("\n=== DXCON STAGING STACK SMOKE ===\n")
    verification = run_staging_verification()
    if not verification["ok"]:
        print("FAIL: staging verification incomplete")
        sys.exit(1)

    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.extensions.db import db

    staging_values = parse_env_file(ROOT / ".env.staging.example")
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "APP_ENV": "staging",
            "CORS_ORIGINS": staging_values.get("CORS_ORIGINS", ""),
            "SQLALCHEMY_DATABASE_URI": staging_values.get("DATABASE_URL", ""),
            "REDIS_URL": staging_values.get("REDIS_URL", ""),
            "SMTP_HOST": staging_values.get("SMTP_HOST", ""),
            "SMTP_PORT": int(staging_values.get("SMTP_PORT", "587")),
            "SMTP_FROM": staging_values.get("SMTP_FROM", ""),
            "STORAGE_PATH": staging_values.get("STORAGE_PATH", "/tmp/dxcon-uploads"),
        }
    )
    client = app.test_client()
    with app.app_context():
        db.create_all()
        steps = {
            "live_probe": client.get("/live").status_code == 200,
            "ready_probe": client.get("/ready").status_code == 200,
            "health_probe": client.get("/api/v1/system/health").status_code == 200,
            "nginx_files": verification["checks"]["nginx_config"]["ok"],
            "docker_stack": verification["checks"]["docker_stack"]["ok"],
            "backup_scripts": verification["checks"]["backup_scripts"]["ok"],
        }
    passed = sum(1 for ok in steps.values() if ok)
    for name, ok in steps.items():
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
    print(f"\nSmoke: {passed}/{len(steps)}")
    if passed != len(steps):
        sys.exit(1)
    print("STAGING STACK SMOKE PASSED\n")


if __name__ == "__main__":
    main()
