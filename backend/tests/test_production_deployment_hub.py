import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class ProductionDeploymentTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        from app.operations.deployment_service import DeploymentService

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        DeploymentService.run_checklist()
        self.client = self.app.test_client()
        user = User(
            email="demo-admin-deploy@demo.dxcon.test",
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

    def test_production_deployment_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/production-deployment",
            "/production-deployment/rollback",
            "/api/v1/production-deployment/dashboard",
            "/api/v1/production-deployment/readiness",
        ):
            self.assertIn(route, routes)

    def test_dashboard_and_features(self):
        response = self.client.get("/production-deployment")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Production Deployment", response.get_data(as_text=True))

        dashboard = self.client.get("/api/v1/production-deployment/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        payload = dashboard.get_json()
        self.assertEqual(payload["phase"], "5.5")
        self.assertEqual(len(payload["features"]), 7)

    def test_legacy_deployment_preserved(self):
        deployment = self.client.get("/api/v1/operations/deployment")
        self.assertEqual(deployment.status_code, 200)
        payload = deployment.get_json()
        if payload.get("success"):
            payload = payload["data"]
        self.assertIsNotNone(payload.get("current_version"))


if __name__ == "__main__":
    unittest.main()
