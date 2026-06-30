import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REPORTING_SEED_ORDERS"] = "30"
os.environ["REPORTING_SEED_TESTS"] = "120"

from app import create_app
from app.extensions.db import db
from app.services.dashboard_platform_service import DashboardPlatformService
from scripts.seed_reporting_demo import seed_reporting_demo


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/dashboard/executive",
        "/api/v1/dashboard/admin",
        "/api/v1/dashboard/lab",
        "/api/v1/dashboard/clinic",
        "/api/v1/dashboard/partner",
        "/api/v1/dashboard/collector",
    ]
    for route in required:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            return False
    return True


def verify_aggregation():
    with app.app_context():
        db.create_all()
        seed_reporting_demo()
        for role in ["EXECUTIVE", "ADMIN", "LAB", "CLINIC", "PARTNER", "COLLECTOR"]:
            payload = DashboardPlatformService.get_dashboard(role, page=1, page_size=10)
            if "widgets" not in payload:
                print("MISSING: widgets for", role)
                return False
            print("OK: dashboard aggregation", role)
        return True


app = create_app()
print("\n=== DXCON DASHBOARD VERIFY ===\n")
errors = 0
if not verify_routes(app):
    errors += 1
if not verify_aggregation():
    errors += 1
if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nDASHBOARD VERIFY PASSED\n")
