#!/usr/bin/env python3
"""Smoke test production blocker endpoints and config guards."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.infrastructure.production_readiness import evaluate_go_live_blockers


def main():
    print("\n=== DXCON PRODUCTION BLOCKERS SMOKE TEST ===\n")
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
    client = app.test_client()

    errors = 0
    endpoints = [
        "/live",
        "/ready",
        "/api/v1/infrastructure/readiness",
        "/api/v1/infrastructure/status",
        "/api/v1/system/health",
    ]
    for path in endpoints:
        response = client.get(path)
        if response.status_code in {200, 503}:
            print("OK:", path, response.status_code)
        else:
            print("FAIL:", path, response.status_code)
            errors += 1

    with app.app_context():
        blockers = evaluate_go_live_blockers(app)
        if blockers["ready"]:
            print("OK: dev/test blocker profile ready")
        else:
            print("FAIL: unexpected dev/test blockers", blockers["blockers"])
            errors += 1

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
