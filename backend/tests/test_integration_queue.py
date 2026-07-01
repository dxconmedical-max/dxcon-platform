import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import INTEGRATION_JOB_DEAD_LETTER, INTEGRATION_JOB_SUCCESS
from app.extensions.db import db
from app.models.integration_platform import IntegrationDeadLetter, IntegrationJob
from app.services.integration_platform_service import IntegrationPlatformService, IntegrationQueueService


class IntegrationQueueTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        IntegrationPlatformService.ensure_defaults()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_job_success(self):
        created = self.client.post(
            "/api/v1/integration-queue/jobs",
            json={"adapter_type": "HIS", "payload": {"patient_id": "P1"}},
        )
        self.assertEqual(created.status_code, 201)
        job_id = created.get_json()["id"]
        processed = IntegrationQueueService.process_job(job_id)
        self.assertEqual(processed["status"], INTEGRATION_JOB_SUCCESS)

    def test_dead_letter_and_replay(self):
        job = IntegrationQueueService.create({"adapter_type": "LIS", "payload": {}, "max_retries": 1})
        IntegrationQueueService.process_job(job["id"], force_fail=True)
        row = IntegrationJob.query.filter_by(id=job["id"]).first()
        self.assertEqual(row.status, INTEGRATION_JOB_DEAD_LETTER)
        dead = IntegrationDeadLetter.query.filter_by(job_id=job["id"]).first()
        replay = self.client.post(f"/api/v1/integration-queue/dead-letters/{dead.id}/replay")
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.get_json()["status"], INTEGRATION_JOB_SUCCESS)


if __name__ == "__main__":
    unittest.main()
