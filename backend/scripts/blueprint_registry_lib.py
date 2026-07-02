"""Blueprint registry verification helpers."""

from __future__ import annotations

import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent


def find_duplicate_routes(app):
    seen = defaultdict(list)
    for rule in app.url_map.iter_rules():
        methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
        key = (str(rule.rule), tuple(methods))
        seen[key].append(rule.endpoint)
    return {str(key): endpoints for key, endpoints in seen.items() if len(endpoints) > 1}


def missing_prefixes(app):
    missing = []
    for rule in app.url_map.iter_rules():
        path = str(rule.rule)
        if path.startswith("/static"):
            continue
        if not path.startswith("/"):
            missing.append(path)
    return missing


def run_blueprint_registry_verification() -> dict:
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    sys.path.insert(0, str(ROOT))

    from app import create_app
    from app.extensions.db import db

    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        duplicates = find_duplicate_routes(app)
        prefixes = missing_prefixes(app)
        blueprint_count = len(app.blueprints)
        route_count = len(list(app.url_map.iter_rules()))
        checks = {
            "app_created": {"ok": app is not None},
            "blueprints_registered": {"ok": blueprint_count >= 50, "count": blueprint_count},
            "routes_registered": {"ok": route_count >= 100, "count": route_count},
            "no_duplicate_routes": {"ok": not duplicates, "count": len(duplicates), "duplicates": duplicates},
            "route_prefixes": {"ok": not prefixes, "missing": prefixes},
        }
    passed = sum(1 for item in checks.values() if item.get("ok"))
    return {"ok": passed == len(checks), "passed": passed, "total": len(checks), "checks": checks}
