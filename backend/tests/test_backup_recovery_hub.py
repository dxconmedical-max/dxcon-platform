import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class BackupRecoveryTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        from app.operations.backup_service import BackupService
        from app.operations.scheduler_service import SchedulerService

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        SchedulerService.ensure_defaults()
        BackupService.run_backup({"backup_type": "DATABASE"})
        self.client = self.app.test_client()
        user = User(
            email="demo-admin-backup@demo.dxcon.test",
            role="ADMIN",
            password_hash=hash_password("DemoPass123!"),
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        with self.client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["email"] = user.email

    def tearDown(self):
        from app.extensions.db import db

        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_backup_recovery_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/backup-recovery",
            "/backup-recovery/runbook",
            "/api/v1/backup-recovery/dashboard",
            "/api/v1/backup-recovery/readiness",
        ):
            self.assertIn(route, routes)

    def test_dashboard_and_readiness(self):
        response = self.client.get("/backup-recovery")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Backup Dashboard", response.get_data(as_text=True))

        dashboard = self.client.get("/api/v1/backup-recovery/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        payload = dashboard.get_json()
        self.assertEqual(payload["phase"], "5.3")
        self.assertEqual(len(payload["features"]), 5)

        readiness = self.client.get("/api/v1/backup-recovery/readiness")
        self.assertEqual(readiness.status_code, 200)
        self.assertIn("sections", readiness.get_json())

    def test_legacy_operations_preserved(self):
        backups = self.client.get("/api/v1/operations/backups")
        self.assertEqual(backups.status_code, 200)
        self.assertGreaterEqual(backups.get_json()["count"], 1)


if __name__ == "__main__":
    unittest.main()
