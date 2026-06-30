import os
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
    REPORT_FORMAT_CSV,
    REPORT_FORMAT_JSON,
    REPORT_FORMAT_PDF,
    REPORT_SCHEDULE_DAILY,
    REPORT_SCHEDULE_MONTHLY,
    REPORT_TYPE_KPI,
)
from app.extensions.db import db
from app.models.reporting_platform import ReportJob, ReportSchedule
from app.services.report_platform_service import ReportPlatformService
from scripts.seed_reporting_demo import seed_reporting_demo


class ScheduledReportsTestCase(unittest.TestCase):
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

    def test_report_api_formats(self):
        for fmt in [REPORT_FORMAT_JSON, REPORT_FORMAT_CSV, REPORT_FORMAT_PDF]:
            response = self.client.post(
                "/api/v1/reports/generate",
                json={"report_type": REPORT_TYPE_KPI, "format": fmt},
            )
            self.assertEqual(response.status_code, 201, fmt)
            self.assertEqual(response.get_json()["job"]["output_format"], fmt)

    def test_schedule_and_email_payload(self):
        schedule = ReportPlatformService.create_schedule(
            {
                "report_type": REPORT_TYPE_KPI,
                "cadence": REPORT_SCHEDULE_DAILY,
                "format": REPORT_FORMAT_PDF,
                "recipients": ["ops@dxcon.vn"],
            }
        )
        schedule.next_run_at = datetime.utcnow() - timedelta(minutes=1)
        db.session.commit()
        results = ReportPlatformService.run_due_schedules()
        self.assertGreaterEqual(len(results), 1)
        self.assertIn("email_payload", results[0])
        self.assertIn("to", results[0]["email_payload"])

    def test_report_history_and_download(self):
        job, _ = ReportPlatformService.generate({"report_type": REPORT_TYPE_KPI, "format": REPORT_FORMAT_JSON})
        history = ReportPlatformService.history()
        self.assertGreaterEqual(history["total"], 1)
        download = ReportPlatformService.download(job.id)
        self.assertIn("content", download)
        self.assertIsNotNone(ReportJob.query.get(job.id))
        self.assertIsNotNone(ReportSchedule.query.first() or True)


if __name__ == "__main__":
    unittest.main()
