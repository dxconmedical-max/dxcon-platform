import os, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

class HealthcareEcosystemTestCase(unittest.TestCase):
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
        user = User(email="demo-healthcare_ecosystem@demo.dxcon.test", role="ADMIN", password_hash=hash_password("DemoPass123!"), is_active=True)
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

    def test_routes_registered(self):
        routes = {str(r.rule) for r in self.app.url_map.iter_rules()}
        self.assertIn("/healthcare-ecosystem", routes)
        self.assertIn("/api/v1/healthcare-ecosystem/dashboard", routes)

    def test_dashboard(self):
        r = self.client.get("/healthcare-ecosystem")
        self.assertEqual(r.status_code, 200)
        d = self.client.get("/api/v1/healthcare-ecosystem/dashboard")
        self.assertEqual(d.status_code, 200)
        payload = d.get_json()
        if isinstance(payload, dict) and payload.get("success"):
            payload = payload["data"]
        self.assertEqual(payload["phase"], "10")
        self.assertEqual(payload["release"]["tag"], "v1.0.0-rc1")

    def test_ecosystem_modules(self):
        from app.services.healthcare_ecosystem_service import FEATURES, RELEASE
        self.assertEqual(len(FEATURES), 25)
        self.assertEqual(RELEASE["version"], "1.0.0-rc1")
