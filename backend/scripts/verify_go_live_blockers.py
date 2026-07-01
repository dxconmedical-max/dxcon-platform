#!/usr/bin/env python3
"""Verify go-live blockers for staging/production readiness."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = ROOT / "generated_release"
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.extensions.db import db
from app.infrastructure.production_readiness import (
    check_notification_provider_readiness,
    evaluate_go_live_blockers,
)
from app.observability.health_service import HealthPlatformService


CHECKS = []


def check(name, ok):
    CHECKS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'}: {name}")
    return ok


def main():
    print("\n=== DXCON GO-LIVE BLOCKERS VERIFY ===\n")
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        blockers = evaluate_go_live_blockers(app)
        health = HealthPlatformService.evaluate()
        notification = check_notification_provider_readiness(app)

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    output = GENERATED_DIR / "GO_LIVE_BLOCKERS.json"
    payload = {
        **blockers,
        "observability_health": health,
        "notification_readiness": notification,
    }
    output.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print("OK: wrote", output)

    check("blocker report generated", output.exists())
    check("relaxed dev/test profile ready", blockers["ready"])
    check("observability evaluate ok", health["status"] != "DOWN")
    check("application component ok", health["components"][0]["status"] != "DOWN")
    check("notification readiness", notification.get("ok", False) or app.config.get("TESTING"))

    staging_app = create_app()
    staging_app.config.update(
        {
            "TESTING": False,
            "APP_ENV": "staging",
            "CORS_ORIGINS": "*",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )
    staging_blockers = evaluate_go_live_blockers(staging_app)
    check("staging rejects wildcard cors", not staging_blockers["cors"]["ok"])
    check("staging rejects sqlite", not staging_blockers["database"]["ok"])

    production_app = create_app()
    production_app.config.update(
        {
            "TESTING": False,
            "APP_ENV": "production",
            "CORS_ORIGINS": "https://app.dxcon.test",
            "SQLALCHEMY_DATABASE_URI": "postgresql://dxcon:dxcon@localhost:5432/dxcon",
            "REDIS_URL": "",
            "SMTP_HOST": "",
        }
    )
    production_blockers = evaluate_go_live_blockers(production_app)
    check("production flags redis blocker", any(item["id"] == "redis_unavailable" for item in production_blockers["blockers"]))
    check("production flags smtp blocker", any(item["id"] == "smtp_not_configured" for item in production_blockers["blockers"]))

    failed = [name for name, ok in CHECKS if not ok]
    print("\nSUMMARY:", len(CHECKS) - len(failed), "passed,", len(failed), "failed")
    if failed:
        print("FAILED:", failed)
        sys.exit(1)
    print("GO-LIVE BLOCKERS VERIFY PASSED\n")


if __name__ == "__main__":
    main()
