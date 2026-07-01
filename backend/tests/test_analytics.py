import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REPORTING_SEED_ORDERS"] = "15"
os.environ["REPORTING_SEED_TESTS"] = "60"

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


class AnalyticsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        seed_reporting_demo()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_analytics_services(self):
        revenue = RevenueAnalyticsService.aggregate()
        self.assertIn("summary", revenue)
        lab = LabAnalyticsService.aggregate()
        self.assertIn("summary", lab)
        transport = TransportAnalyticsService.aggregate()
        self.assertIn("summary", transport)
        collector = CollectorAnalyticsService.aggregate()
        self.assertIn("summary", collector)
        partner = PartnerAnalyticsService.aggregate()
        self.assertIn("summary", partner)
        clinic = ClinicAnalyticsService.aggregate()
        self.assertIn("summary", clinic)
        system = SystemAnalyticsService.aggregate()
        self.assertIn("orders", system)

    def test_metric_snapshots(self):
        before = MetricSnapshot.query.count()
        RevenueAnalyticsService.aggregate()
        self.assertGreater(MetricSnapshot.query.count(), before)


if __name__ == "__main__":
    unittest.main()
