import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.operations_platform import BackupJob


class OperationsBackupTestCase(unittest.TestCase):
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

    def test_backup_and_restore_dry_run(self):
        run = self.client.post("/api/v1/operations/backups/run", json={"backup_type": "DATABASE"})
        self.assertEqual(run.status_code, 201)
        backup_id = run.get_json()["backup"]["id"]

        validate = self.client.post(f"/api/v1/operations/backups/{backup_id}/validate")
        self.assertEqual(validate.status_code, 200)
        self.assertTrue(validate.get_json()["valid"])

        dry_run = self.client.post("/api/v1/operations/restores/dry-run", json={"backup_id": backup_id})
        self.assertEqual(dry_run.status_code, 201)
        self.assertEqual(dry_run.get_json()["restore"]["mode"], "DRY_RUN")
        self.assertGreaterEqual(BackupJob.query.count(), 1)


if __name__ == "__main__":
    unittest.main()
