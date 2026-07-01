import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REPORTING_SEED_ORDERS"] = "50"
os.environ["REPORTING_SEED_TESTS"] = "200"
os.environ["REPORTING_SEED_COLLECTORS"] = "20"
os.environ["REPORTING_SEED_LABS"] = "10"
os.environ["REPORTING_SEED_CLINICS"] = "15"
os.environ["REPORTING_SEED_PARTNERS"] = "25"
os.environ["REPORTING_SEED_MONTHS"] = "24"

from app import create_app
from app.extensions.db import db
from app.models.reporting_platform import (
    ClinicAnalytics,
    CollectorAnalytics,
    DashboardLayout,
    DashboardWidget,
    KPIRecord,
    LabAnalytics,
    MetricSnapshot,
    PartnerAnalytics,
    ReportDefinition,
    ReportJob,
    ReportSchedule,
    RevenueAnalytics,
)
from app.services.report_platform_service import ReportPlatformService
from app.services.reporting_service import ExecutiveDashboardService, ReportingService
from scripts.seed_reporting_demo import seed_reporting_demo


def verify_models_import():
    models = [
        ReportDefinition,
        ReportJob,
        ReportSchedule,
        DashboardWidget,
        DashboardLayout,
        KPIRecord,
        MetricSnapshot,
        RevenueAnalytics,
        LabAnalytics,
        CollectorAnalytics,
        PartnerAnalytics,
        ClinicAnalytics,
    ]
    for model in models:
        assert model.__tablename__
        print("OK: model", model.__name__)
    return True


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/reports",
        "/api/v1/reports/generate",
        "/api/v1/reports/history",
        "/api/v1/reports/download",
        "/api/v1/reports/schedule",
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


def verify_no_duplicate_report_routes(app):
    report_routes = [str(rule) for rule in app.url_map.iter_rules() if "/api/v1/reports" in str(rule)]
    if len(report_routes) != len(set(report_routes)):
        print("DUPLICATE: report routes detected")
        return False
    print("OK: no duplicate report routes")
    return True


def verify_seed_and_flow():
    with app.app_context():
        db.create_all()
        summary = seed_reporting_demo()
        if summary["orders_created"] < 1:
            print("MISSING: reporting demo orders")
            return False
        print("OK: reporting demo seed", summary["orders_created"], "orders")

        if summary["snapshots_created"] < 24:
            print("MISSING: analytics snapshots", summary["snapshots_created"])
            return False
        print("OK: analytics snapshots", summary["snapshots_created"])

        job, _ = ReportPlatformService.generate({"report_type": "KPI", "format": "JSON"})
        if job.status != "COMPLETED":
            print("MISSING: report generation")
            return False
        print("OK: report generation")

        kpi = ReportingService.daily_booking_report()
        if "total" not in kpi:
            print("MISSING: daily booking report data")
            return False
        print("OK: daily booking report")

        dashboard = ExecutiveDashboardService.get_dashboard()
        if "kpi" not in dashboard:
            print("MISSING: executive dashboard")
            return False
        print("OK: executive dashboard")

        schedules = ReportPlatformService.list_schedules()
        if schedules["total"] < 0:
            print("MISSING: scheduled reports listing")
            return False
        print("OK: scheduled reports")
        return True


app = create_app()
print("\n=== DXCON REPORTING VERIFY ===\n")
errors = 0
if not verify_models_import():
    errors += 1
if not verify_routes(app):
    errors += 1
if not verify_no_duplicate_report_routes(app):
    errors += 1
if not verify_seed_and_flow():
    errors += 1
if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nREPORTING VERIFY PASSED\n")
