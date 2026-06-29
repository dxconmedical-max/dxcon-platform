import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.services.reporting_service import ExecutiveDashboardService, ReportingService
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_reporting_demo import seed_reporting_demo
from scripts.seed_scheduling_demo import seed_scheduling_demo


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/reports/kpi",
        "/api/v1/reports/revenue",
        "/api/v1/reports/operations",
        "/api/v1/reports/partners",
        "/api/v1/reports/collectors",
        "/reports",
        "/reports/executive",
        "/reports/operations",
    ]
    for route in required:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            return False
    return True


def verify_seed_and_flow():
    with app.app_context():
        db.create_all()
        seed_marketplace_demo()
        seed_scheduling_demo()
        summary = seed_reporting_demo()
        if summary["orders_created"] < 1:
            print("MISSING: reporting demo orders")
            return False
        print("OK: reporting demo seed")

        kpi = ReportingService.daily_booking_report()
        if kpi["total"] < 1:
            print("MISSING: daily booking report data")
            return False
        print("OK: daily booking report")

        dashboard = ExecutiveDashboardService.get_dashboard()
        if "kpi" not in dashboard:
            print("MISSING: executive dashboard")
            return False
        print("OK: executive dashboard")
        return True


app = create_app()
print("\n=== DXCON REPORTING VERIFY ===\n")
errors = 0
if not verify_routes(app):
    errors += 1
if not verify_seed_and_flow():
    errors += 1
if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nREPORTING VERIFY PASSED\n")
