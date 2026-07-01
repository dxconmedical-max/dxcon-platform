#!/usr/bin/env python3
"""Generate API v1 inventory artifacts for Go-Live Sprint Day 1."""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_DIR = ROOT / "inventory"
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app

DEPRECATED_PREFIXES = (
    "/api/v2/",
    "/api/v1/notification-templates",
    "/api/v1/admin-security",
)

LEGACY_WEB_PREFIXES = (
    "/notification-templates",
    "/executive-v8",
)

UNUSED_HINTS = (
    "/api/v1/_observability/",
)


def _methods(rule):
    return sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})


def _blueprint_name(endpoint):
    return endpoint.split(".")[0] if "." in endpoint else endpoint


def build_inventories(app):
    routes = []
    api_v1 = []
    duplicates = []
    legacy = []
    deprecated = []
    missing_prefix = []
    route_map = defaultdict(list)
    endpoint_deps = defaultdict(list)

    for rule in app.url_map.iter_rules():
        path = str(rule)
        methods = _methods(rule)
        entry = {
            "path": path,
            "methods": methods,
            "endpoint": rule.endpoint,
            "blueprint": _blueprint_name(rule.endpoint),
        }
        routes.append(entry)
        route_map[(path, tuple(methods))].append(rule.endpoint)
        endpoint_deps[entry["blueprint"]].append(
            {"path": path, "methods": methods, "endpoint": rule.endpoint}
        )

        if path.startswith("/api/v1/"):
            api_v1.append(entry)
        elif path.startswith("/api/") and not path.startswith("/api/v1/"):
            missing_prefix.append(entry)

        if any(path.startswith(prefix) for prefix in DEPRECATED_PREFIXES):
            deprecated.append(entry)
        if any(path == prefix or path.startswith(prefix + "/") for prefix in LEGACY_WEB_PREFIXES):
            legacy.append(entry)
        if any(hint in path for hint in UNUSED_HINTS):
            legacy.append(entry)

    for key, endpoints in route_map.items():
        if len(endpoints) > 1:
            duplicates.append({"route": key[0], "methods": list(key[1]), "endpoints": endpoints})

    generated_at = datetime.now(timezone.utc).isoformat()

    api_inventory = {
        "generated_at": generated_at,
        "api_version": "v1",
        "frozen": True,
        "total_v1_endpoints": len(api_v1),
        "endpoints": sorted(api_v1, key=lambda item: (item["path"], ",".join(item["methods"]))),
        "deprecated": deprecated,
        "legacy": legacy,
        "missing_v1_prefix": missing_prefix,
        "duplicate_routes": duplicates,
        "summary": {
            "duplicate_count": len(duplicates),
            "deprecated_count": len(deprecated),
            "legacy_count": len(legacy),
            "missing_prefix_count": len(missing_prefix),
        },
    }

    route_inventory = {
        "generated_at": generated_at,
        "total_routes": len(routes),
        "routes": sorted(routes, key=lambda item: (item["path"], ",".join(item["methods"]))),
        "duplicate_routes": duplicates,
    }

    prefix_counts = defaultdict(int)
    for item in routes:
        parts = item["path"].split("/")
        prefix = parts[1] if len(parts) > 1 else item["path"]
        prefix_counts[prefix] += 1
    route_inventory["prefix_counts"] = dict(sorted(prefix_counts.items(), key=lambda x: (-x[1], x[0])))

    endpoint_dependency = {
        "generated_at": generated_at,
        "blueprint_count": len(endpoint_deps),
        "dependencies": {
            blueprint: sorted(routes, key=lambda item: item["path"])
            for blueprint, routes in sorted(endpoint_deps.items())
        },
    }

    return api_inventory, route_inventory, endpoint_dependency


def write_inventory(app):
    INVENTORY_DIR.mkdir(parents=True, exist_ok=True)
    api_inventory, route_inventory, endpoint_dependency = build_inventories(app)

    files = {
        "api_inventory.json": api_inventory,
        "route_inventory.json": route_inventory,
        "endpoint_dependency.json": endpoint_dependency,
    }

    for name, payload in files.items():
        path = INVENTORY_DIR / name
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print("WROTE:", path)

    return api_inventory


def main():
    app = create_app()
    inventory = build_inventories(app)[0]

    print("\n=== DXCON API INVENTORY GENERATION ===\n")
    print("API v1 endpoints:", inventory["total_v1_endpoints"])
    print("Duplicate routes:", inventory["summary"]["duplicate_count"])
    print("Deprecated routes:", inventory["summary"]["deprecated_count"])
    print("Legacy routes:", inventory["summary"]["legacy_count"])

    write_inventory(app)

    if inventory["summary"]["duplicate_count"] > 0:
        print("\nFAILED: duplicate routes detected")
        sys.exit(1)

    print("\nAPI INVENTORY GENERATION PASSED\n")


if __name__ == "__main__":
    main()
