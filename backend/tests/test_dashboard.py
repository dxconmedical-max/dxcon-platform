import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REPORTING_SEED_ORDERS"] = "20"
os.environ["REPORTING_SEED_TESTS"] = "80"
os.environ["REPORTING_SEED_COLLECTORS"] = "10"
os.environ["REPORTING_SEED_LABS"] = "5"
os.environ["REPORTING_SEED_CLINICS"] = "8"
os.environ["REPORTING_SEED_PARTNERS"] = "12"
os.environ["REPORTING_SEED_MONTHS"] = "24"

from app import create_app
from app.extensions.db import db
from app.models.reporting_platform import ReportDefinition, ReportJob
from app.services.report_platform_service import ReportPlatformService
from scripts.seed_reporting_demo import seed_reporting_demo


class DashboardApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        seed_reporting_demo()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_dashboard_endpoints(self):
        for path in [
            "/api/v1/dashboard/executive",
            "/api/v1/dashboard/admin",
            "/api/v1/dashboard/lab",
            "/api/v1/dashboard/clinic",
            "/api/v1/dashboard/partner",
            "/api/v1/dashboard/collector",
        ]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            payload = response.get_json()
            self.assertIn("dashboard_role", payload)
            self.assertIn("widgets", payload)
            self.assertIn("pagination", payload)

    def test_dashboard_pagination_filters(self):
        response = self.client.get("/api/v1/dashboard/executive?page=1&page_size=5")
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.get_json()["widgets"]), 5)


if __name__ == "__main__":
    unittest.main()
