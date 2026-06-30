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
from app.core.statuses import (
    KPI_CODE_ORDERS,
    KPI_CODE_REVENUE,
    KPI_CODE_TESTS,
    KPI_PERIOD_DAILY,
    KPI_PERIOD_MONTHLY,
    KPI_PERIOD_QUARTERLY,
    KPI_PERIOD_WEEKLY,
    KPI_PERIOD_YEARLY,
)
from app.extensions.db import db
from app.models.reporting_platform import KPIRecord
from app.services.kpi_engine_service import KPIEngineService
from scripts.seed_reporting_demo import seed_reporting_demo


class KPITestCase(unittest.TestCase):
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

    def test_kpi_periods(self):
        for period in [
            KPI_PERIOD_DAILY,
            KPI_PERIOD_WEEKLY,
            KPI_PERIOD_MONTHLY,
            KPI_PERIOD_QUARTERLY,
            KPI_PERIOD_YEARLY,
        ]:
            payload = KPIEngineService.compute_period(period, persist=True)
            self.assertEqual(payload["period_type"], period)
            self.assertIn("metrics", payload)
            self.assertGreaterEqual(payload["metrics"][KPI_CODE_ORDERS], 0)

    def test_kpi_metric_coverage(self):
        payload = KPIEngineService.compute_monthly(persist=True)
        metrics = payload["metrics"]
        for code in [
            KPI_CODE_ORDERS,
            KPI_CODE_TESTS,
            KPI_CODE_REVENUE,
            "COLLECTOR_UTILIZATION",
            "TRANSPORT_TIME",
            "TAT",
            "SLA",
            "CRITICAL_RESULTS",
            "AI_INTERPRETATION",
            "DOCTOR_REVIEW_TIME",
        ]:
            self.assertIn(code, metrics)
        self.assertGreater(KPIRecord.query.count(), 0)

    def test_kpi_list_records(self):
        KPIEngineService.compute_daily(persist=True)
        listing = KPIEngineService.list_records(page=1, page_size=10)
        self.assertGreaterEqual(listing["total"], 1)


if __name__ == "__main__":
    unittest.main()
