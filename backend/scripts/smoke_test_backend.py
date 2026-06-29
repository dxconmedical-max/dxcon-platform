import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.company import Company


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

KEY_APIS = [
    "/api/v1/system/health",
    "/api/v1/marketplace/search",
    "/api/v1/billing/invoices",
    "/api/v1/payments",
    "/api/v1/integrations/connections",
    "/api/v1/iot/devices",
    "/api/v1/doctor/dashboard",
    "/api/v1/clinic/dashboard",
    "/api/v1/patient/dashboard",
]


def main():
    print("\n=== DXCON BACKEND SMOKE TEST ===\n")
    errors = 0

    try:
        app = create_app()
        print("OK: app factory starts")
    except Exception as exc:
        print("FAIL: app factory", exc)
        sys.exit(1)

    with app.app_context():
        try:
            db.create_all()
            db.session.add(Company(company_code="SMOKE", company_name="Smoke Test Co", tax_code="01"))
            db.session.commit()
            db.session.execute(db.text("SELECT 1"))
            print("OK: database connects")
        except Exception as exc:
            print("FAIL: database", exc)
            errors += 1

    client = app.test_client()

    home = client.get("/")
    if home.status_code in (200, 302, 308):
        print("OK: home route responds")
    else:
        print("FAIL: home route status", home.status_code)
        errors += 1

    registered = {name for name in app.blueprints.keys()}
    missing = [name for name in CORE_BLUEPRINTS if name not in registered]
    if missing:
        print("FAIL: missing core blueprints", missing)
        errors += 1
    else:
        print("OK: core blueprints registered")

    routes = {rule.rule for rule in app.url_map.iter_rules()}
    for route in KEY_APIS:
        if route in routes:
            print("OK: route registered", route)
        else:
            print("MISSING: route", route)
            errors += 1

    for route in KEY_APIS:
        if route not in routes:
            continue
        response = client.get(route)
        if response.status_code >= 500:
            print("FAIL: API 5xx", route, response.status_code)
            errors += 1
        else:
            print("OK: API reachable", route, response.status_code)

    if errors:
        print("\nSMOKE TEST FAILED:", errors, "issue(s)")
        sys.exit(1)

    print("\nBACKEND SMOKE TEST PASSED\n")


if __name__ == "__main__":
    main()
