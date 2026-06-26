import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app

app = create_app()

required_routes = [
    "/api/v1/shipments",
    "/shipments",
    "/api/v1/logistics-v2/events",
    "/logistics-v2",
]

routes = {str(r) for r in app.url_map.iter_rules()}

print("\n=== DXCON LOGISTICS V2 VERIFY ===\n")

errors = 0

for route in required_routes:
    if route in routes:
        print("OK:", route)
    else:
        print("MISSING:", route)
        errors += 1

if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)

print("\nLOGISTICS V2 VERIFY PASSED\n")
