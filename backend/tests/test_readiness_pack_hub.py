import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class ReadinessPackTestCase(unittest.TestCase):
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
            email="demo-admin-readiness-pack@demo.dxcon.test",
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

    def test_readiness_pack_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/readiness-pack",
            "/readiness-pack/roadmap",
            "/api/v1/readiness-pack/dashboard",
            "/api/v1/readiness-pack/readiness",
        ):
            self.assertIn(route, routes)

    def test_dashboard_and_artifacts(self):
        from app.services.readiness_pack_service import write_generated_artifacts

        write_generated_artifacts()

        response = self.client.get("/readiness-pack")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Readiness Pack", response.get_data(as_text=True))

        dashboard = self.client.get("/api/v1/readiness-pack/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        payload = dashboard.get_json()
        self.assertEqual(payload["phase"], "5.14")
        self.assertEqual(len(payload["features"]), 6)

        self.assertTrue((REPO / "docs" / "KNOWN_LIMITATIONS.md").exists())
        self.assertTrue((REPO / "docs" / "ROADMAP_v2.md").exists())
        self.assertTrue((ROOT / "generated_release" / "SYSTEM_READINESS_REPORT.json").exists())

    def test_legacy_pages_preserved(self):
        checklist = self.client.get("/pilot-checklist")
        self.assertEqual(checklist.status_code, 200)
        security = self.client.get("/security-compliance")
        self.assertEqual(security.status_code, 200)


if __name__ == "__main__":
    unittest.main()
