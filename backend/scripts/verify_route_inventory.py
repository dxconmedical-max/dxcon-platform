import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app


CORE_BLUEPRINTS = [
    "marketplace",
    "billing",
    "payments",
    "integrations",
    "iot",
    "doctor_portal",
    "clinic_portal",
    "patient_portal",
    "system",
]


def _route_key(rule):
    methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
    return rule.rule, tuple(methods)


def analyze_routes(app):
    duplicate_routes = []
    route_map = defaultdict(list)
    endpoint_counts = Counter()
    prefix_counts = Counter()

    for rule in app.url_map.iter_rules():
        route_map[_route_key(rule)].append(rule.endpoint)
        endpoint_counts[rule.endpoint] += 1

        prefix = rule.rule.split("/")[1] if rule.rule.startswith("/") and len(rule.rule.split("/")) > 1 else rule.rule
        prefix_counts[prefix or "/"] += 1

    for key, endpoints in route_map.items():
        if len(endpoints) > 1:
            duplicate_routes.append({"route": key[0], "methods": list(key[1]), "endpoints": endpoints})

    duplicate_endpoints = [
        {"endpoint": endpoint, "count": count}
        for endpoint, count in endpoint_counts.items()
        if count > 1
    ]

    registered_blueprints = sorted({bp.name for bp in app.blueprints.values()})
    missing_core = [name for name in CORE_BLUEPRINTS if name not in registered_blueprints]

    return {
        "total_routes": len(list(app.url_map.iter_rules())),
        "duplicate_routes": duplicate_routes,
        "duplicate_endpoints": duplicate_endpoints,
        "prefix_counts": dict(sorted(prefix_counts.items(), key=lambda item: (-item[1], item[0]))),
        "registered_blueprints": registered_blueprints,
        "missing_core_blueprints": missing_core,
    }


def main():
    app = create_app()
    report = analyze_routes(app)

    print("\n=== DXCON ROUTE INVENTORY VERIFY ===\n")
    print("Total routes:", report["total_routes"])
    print("Registered blueprints:", len(report["registered_blueprints"]))

    print("\nRoute count by prefix:")
    for prefix, count in list(report["prefix_counts"].items())[:20]:
        print(f"  {prefix}: {count}")
    if len(report["prefix_counts"]) > 20:
        print(f"  ... and {len(report['prefix_counts']) - 20} more prefixes")

    errors = 0

    if report["duplicate_routes"]:
        print("\nDUPLICATE ROUTES:")
        for item in report["duplicate_routes"][:10]:
            print(" ", item)
        errors += 1
    else:
        print("\nOK: no duplicate route/method pairs")

    if report["duplicate_endpoints"]:
        print("\nDUPLICATE ENDPOINT NAMES:")
        for item in report["duplicate_endpoints"][:10]:
            print(" ", item)
        errors += 1
    else:
        print("OK: no duplicate endpoint names")

    if report["missing_core_blueprints"]:
        print("\nMISSING CORE BLUEPRINTS:", report["missing_core_blueprints"])
        errors += 1
    else:
        print("OK: core blueprints registered")

    if errors:
        print("\nROUTE INVENTORY FAILED:", errors, "issue(s)")
        sys.exit(1)

    print("\nROUTE INVENTORY VERIFY PASSED\n")


if __name__ == "__main__":
    main()
