import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.operations_platform import ScheduledJobRun
from app.operations.scheduler_service import SchedulerService


class OperationsSchedulerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        SchedulerService.ensure_defaults()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_scheduler_api(self):
        listing = self.client.get("/api/v1/operations/jobs")
        self.assertEqual(listing.status_code, 200)
        self.assertGreaterEqual(listing.get_json()["count"], 4)

        job_id = listing.get_json()["jobs"][0]["id"]
        run = self.client.post(f"/api/v1/operations/jobs/{job_id}/run")
        self.assertEqual(run.status_code, 200)
        self.assertGreaterEqual(ScheduledJobRun.query.count(), 1)

        runs = self.client.get(f"/api/v1/operations/jobs/{job_id}/runs")
        self.assertEqual(runs.status_code, 200)


if __name__ == "__main__":
    unittest.main()
