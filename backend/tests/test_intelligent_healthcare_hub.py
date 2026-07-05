import os, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

class IntelligentHealthcareTestCase(unittest.TestCase):
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
        user = User(email="demo-intelligent_healthcare@demo.dxcon.test", role="ADMIN", password_hash=hash_password("DemoPass123!"), is_active=True)
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
        self.assertIn("/intelligent-healthcare", routes)
        self.assertIn("/api/v1/intelligent-healthcare/dashboard", routes)

    def test_dashboard(self):
        r = self.client.get("/intelligent-healthcare")
        self.assertEqual(r.status_code, 200)
        d = self.client.get("/api/v1/intelligent-healthcare/dashboard")
        self.assertEqual(d.status_code, 200)
        payload = d.get_json()
        if isinstance(payload, dict) and payload.get("success"):
            payload = payload["data"]
        self.assertEqual(payload["phase"], "8")
        self.assertTrue(payload.get("policy", {}).get("human_review_required"))

    def test_governance_policy(self):
        from app.services.intelligent_healthcare_service import FEATURES, GOVERNANCE_POLICY
        self.assertEqual(len(FEATURES), 31)
        self.assertTrue(GOVERNANCE_POLICY["human_review_required"])
        self.assertFalse(GOVERNANCE_POLICY["automatic_diagnosis"])
