import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REPORTING_SEED_ORDERS"] = "30"
os.environ["REPORTING_SEED_TESTS"] = "120"
os.environ["REPORTING_SEED_MONTHS"] = "24"

from app import create_app
from app.extensions.db import db
from app.models.reporting_platform import MetricSnapshot
from app.services.analytics_engine_service import (
    ClinicAnalyticsService,
    CollectorAnalyticsService,
    LabAnalyticsService,
    PartnerAnalyticsService,
    RevenueAnalyticsService,
    SystemAnalyticsService,
    TransportAnalyticsService,
)
from scripts.seed_reporting_demo import seed_reporting_demo


def verify_analytics():
    with app.app_context():
        db.create_all()
        summary = seed_reporting_demo()
        if summary["snapshots_created"] < 24:
            print("MISSING: analytics snapshots", summary["snapshots_created"])
            return False
        print("OK: seeded snapshots", summary["snapshots_created"])

        services = [
            ("revenue", RevenueAnalyticsService.aggregate),
            ("lab", LabAnalyticsService.aggregate),
            ("transport", TransportAnalyticsService.aggregate),
            ("collector", CollectorAnalyticsService.aggregate),
            ("partner", PartnerAnalyticsService.aggregate),
            ("clinic", ClinicAnalyticsService.aggregate),
            ("system", SystemAnalyticsService.aggregate),
        ]
        before = MetricSnapshot.query.count()
        for name, fn in services:
            result = fn()
            if not result:
                print("MISSING: analytics service", name)
                return False
            print("OK: analytics service", name)
        if MetricSnapshot.query.count() <= before:
            print("MISSING: new metric snapshots from services")
            return False
        print("OK: metric snapshots updated", MetricSnapshot.query.count())
        return True


app = create_app()
print("\n=== DXCON ANALYTICS VERIFY ===\n")
if not verify_analytics():
    print("\nANALYTICS VERIFY FAILED\n")
    sys.exit(1)
print("\nANALYTICS VERIFY PASSED\n")
