import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app

app = create_app()

url_map = defaultdict(list)
endpoint_map = defaultdict(list)

for rule in app.url_map.iter_rules():
    route = str(rule)
    endpoint = rule.endpoint
    methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))

    url_map[route].append((endpoint, methods))
    endpoint_map[endpoint].append((route, methods))

print("\n=== DXCON ROUTE CHECK ===\n")

errors = 0

LEGACY_DUPLICATE_URL_ALLOWLIST = {
    "/collector",
    "/dispatch",
    "/executive",
}

for route, items in url_map.items():

    methods_seen = set()

    for endpoint, methods in items:

        if methods in methods_seen:
            if route in LEGACY_DUPLICATE_URL_ALLOWLIST:
                print("WARN legacy duplicate URL:", route, items)
            else:
                print("REAL DUPLICATE URL:", route, items)
                errors += 1

        methods_seen.add(methods)

for endpoint, items in endpoint_map.items():
    if len(items) > 1:
        print("DUPLICATE ENDPOINT:", endpoint, items)
        errors += 1

required = [
    "/",
    "/monitor",
    "/audit",
    "/security",
    "/finance",
    "/executive-v9",
    "/result-files",
    "/result-files/new",
    "/api/v1/system/health",
    "/api/v1/system/stats",
    "/api/v1/system/routes",
    "/api/v1/system/backup-status",
    "/api/v1/result-files",
]

routes = set(url_map.keys())

for r in required:
    if r not in routes:
        print("MISSING REQUIRED ROUTE:", r)
        errors += 1
    else:
        print("OK:", r)

print("\nTOTAL ROUTES:", len(routes))

if errors:
    print("\nROUTE CHECK FAILED:", errors, "issue(s)")
    sys.exit(1)

print("\nROUTE CHECK PASSED\n")
