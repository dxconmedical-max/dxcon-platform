import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class OperationsRunbooksTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()
        user = User(
            email="demo-admin-runbooks@demo.dxcon.test",
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

    def test_operations_runbooks_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/operations-runbooks",
            "/operations-runbooks/incident",
            "/api/v1/operations-runbooks/dashboard",
            "/api/v1/operations-runbooks/readiness",
        ):
            self.assertIn(route, routes)

    def test_dashboard_and_runbooks(self):
        response = self.client.get("/operations-runbooks")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Operations Runbooks", response.get_data(as_text=True))

        dashboard = self.client.get("/api/v1/operations-runbooks/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        payload = dashboard.get_json()
        self.assertEqual(payload["phase"], "5.11")
        self.assertEqual(len(payload["features"]), 5)

        for name in (
            "GO_LIVE_RUNBOOK.md",
            "BACKUP_RUNBOOK.md",
            "RESTORE_RUNBOOK.md",
            "ROLLBACK_RUNBOOK.md",
            "INCIDENT_RUNBOOK.md",
        ):
            self.assertTrue((REPO / "docs" / name).exists(), msg=f"missing {name}")

        go_live = self.client.get("/api/v1/operations-runbooks/go-live")
        self.assertTrue(go_live.get_json().get("exists"))

    def test_legacy_backup_recovery_preserved(self):
        runbook = self.client.get("/backup-recovery/runbook")
        self.assertEqual(runbook.status_code, 200)


if __name__ == "__main__":
    unittest.main()
