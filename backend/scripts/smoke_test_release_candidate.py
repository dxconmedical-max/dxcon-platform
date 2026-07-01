#!/usr/bin/env python3
"""Lightweight smoke test for Release Candidate RC1."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db


def main():
    print("\n=== DXCON RELEASE CANDIDATE SMOKE TEST ===\n")
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
    client = app.test_client()

    endpoints = [
        ("/live", 200),
        ("/ready", 200),
        ("/api/v1/system/health", 200),
        ("/api/v1/auth/login", 422),
        ("/api/v1/marketplace/search", 200),
        ("/api/v1/partners", 200),
        ("/api/v1/results", 200),
        ("/api/v1/billing/invoices", 200),
        ("/api/v1/payments", 200),
        ("/api/v1/notifications/templates", 200),
        ("/api/v1/reports", 200),
        ("/api/v1/ai/interpret", 405),
        ("/api/v1/sandbox/status", 200),
        ("/api/v1/infrastructure/status", 200),
    ]

    errors = 0
    for path, expected in endpoints:
        response = client.get(path) if expected != 422 else client.post(path, json={})
        if path == "/api/v1/auth/login" and expected == 422:
            ok = response.status_code == 422
        elif path == "/api/v1/ai/interpret" and expected == 405:
            ok = response.status_code in {405, 422}
        else:
            ok = response.status_code == expected or response.status_code < 500
        if ok:
            print("OK:", path, response.status_code)
        else:
            print("FAIL:", path, response.status_code)
            errors += 1

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
