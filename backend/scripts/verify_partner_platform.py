import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app

app = create_app()

required_routes = [
    "/api/v1/partners",
    "/partners",
    "/partners/new",
]

workflow_routes = [
    "/api/v1/partners/<partner_id>/submit",
    "/api/v1/partners/<partner_id>/review",
    "/api/v1/partners/<partner_id>/activate",
    "/api/v1/partners/<partner_id>/verification",
    "/api/v1/partners/<partner_id>/credentials",
    "/api/v1/partners/<partner_id>/users",
]

routes = {str(r) for r in app.url_map.iter_rules()}

print("\n=== DXCON PARTNER PLATFORM VERIFY ===\n")

errors = 0

for route in required_routes:
    if route in routes:
        print("OK:", route)
    else:
        print("MISSING:", route)
        errors += 1

for route in workflow_routes:
    if route in routes:
        print("OK:", route)
    else:
        print("MISSING:", route)
        errors += 1

detail_route_found = any(
    rule.rule.startswith("/partners/<partner_id>")
    for rule in app.url_map.iter_rules()
)

if detail_route_found:
    print("OK: /partners/<partner_id>")
else:
    print("MISSING: /partners/<partner_id>")
    errors += 1

approve_route_found = any(
    "/approve" in rule.rule and "/partners/" in rule.rule
    for rule in app.url_map.iter_rules()
)

if approve_route_found:
    print("OK: partner approve route")
else:
    print("MISSING: partner approve route")
    errors += 1

reject_route_found = any(
    "/reject" in rule.rule and "/partners/" in rule.rule
    for rule in app.url_map.iter_rules()
)

if reject_route_found:
    print("OK: partner reject route")
else:
    print("MISSING: partner reject route")
    errors += 1

services_route_found = any(
    rule.rule.endswith("/services") and "/partners/" in rule.rule
    for rule in app.url_map.iter_rules()
)

if services_route_found:
    print("OK: partner services route")
else:
    print("MISSING: partner services route")
    errors += 1

if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)

print("\nPARTNER PLATFORM VERIFY PASSED\n")
