import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_report_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"


class ReportSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.extensions.db import db

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        with cls.app.app_context():
            db.create_all()

    def test_empty_database_gives_zeroes_not_errors(self):
        from app.executive_platform.service import report_summary

        with self.app.app_context():
            data = report_summary()
        self.assertEqual(data["orders_total"], 0)
        self.assertEqual(data["revenue_total"], 0.0)
        self.assertEqual(len(data["daily"]), 30)
        self.assertEqual(data["top_tests"], [])

    def test_bad_ranges_are_rejected(self):
        from app.executive_platform.service import ExecutivePlatformError, report_summary

        with self.app.app_context():
            with self.assertRaises(ExecutivePlatformError):
                report_summary("2026-11-10", "2026-11-01")
            with self.assertRaises(ExecutivePlatformError):
                report_summary("not-a-date", None)
            with self.assertRaises(ExecutivePlatformError):
                report_summary("2020-01-01", "2026-11-01")

    def test_dashboard_has_no_invented_numbers(self):
        from app.executive_platform.service import executive_dashboard

        with self.app.app_context():
            data = executive_dashboard()
        lab = data["charts"]["laboratory_performance"]
        self.assertIsNone(lab["tat_hours_avg"])
        self.assertIsNone(data["charts"]["collection_performance"]["on_time_pct"])

    def test_endpoints_require_login(self):
        client = self.app.test_client()
        self.assertIn(client.get("/api/v1/executive-platform/report/summary").status_code, (401, 403))
        self.assertIn(client.get("/api/v1/clinic-results/orders").status_code, (401, 403))


if __name__ == "__main__":
    unittest.main()
