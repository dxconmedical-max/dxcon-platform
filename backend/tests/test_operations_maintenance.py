import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.operations.maintenance_service import MaintenanceService


class OperationsMaintenanceTestCase(unittest.TestCase):
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

    def test_maintenance_mode(self):
        status = self.client.get("/api/v1/operations/maintenance")
        self.assertEqual(status.status_code, 200)

        enable = self.client.post("/api/v1/operations/maintenance/enable", json={"title": "Test maintenance"})
        self.assertEqual(enable.status_code, 200)
        self.assertTrue(MaintenanceService.is_active())

        blocked = self.client.post("/api/v1/operations/backups/run", json={"backup_type": "DATABASE"})
        self.assertEqual(blocked.status_code, 503)

        disable = self.client.post("/api/v1/operations/maintenance/disable")
        self.assertEqual(disable.status_code, 200)
        self.assertFalse(MaintenanceService.is_active())


if __name__ == "__main__":
    unittest.main()
