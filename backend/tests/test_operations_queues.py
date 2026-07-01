import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.integration_platform import IntegrationDeadLetter, IntegrationJob


class OperationsQueuesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_queue_operations(self):
        job = IntegrationJob(
            job_code="OPS-Q-001",
            adapter_type="DEMO",
            direction="OUTBOUND",
            status="FAILED",
            payload_json='{"demo": true}',
        )
        db.session.add(job)
        db.session.flush()
        dead = IntegrationDeadLetter(job_id=job.id, reason="demo", payload_json='{"demo": true}')
        db.session.add(dead)
        db.session.commit()

        summary = self.client.get("/api/v1/operations/queues")
        self.assertEqual(summary.status_code, 200)

        dead_letters = self.client.get("/api/v1/operations/queues/dead-letters")
        self.assertEqual(dead_letters.status_code, 200)
        dead_id = dead_letters.get_json()["dead_letters"][0]["id"]

        replay = self.client.post(f"/api/v1/operations/queues/dead-letters/{dead_id}/replay")
        self.assertEqual(replay.status_code, 200)
        self.assertTrue(replay.get_json()["replayed"])


if __name__ == "__main__":
    unittest.main()
