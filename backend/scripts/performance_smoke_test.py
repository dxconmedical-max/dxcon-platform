#!/usr/bin/env python3
"""Performance smoke test for Release Candidate RC1."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from scripts.go_live_rc1_lib import run_performance_smoke


def main():
    print("\n=== DXCON PERFORMANCE SMOKE TEST ===\n")
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
    client = app.test_client()
    result = run_performance_smoke(app, client)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
