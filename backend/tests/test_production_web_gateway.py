"""Production web gateway tests — Sprint 011."""

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class ProductionWebGatewayTestCase(unittest.TestCase):
    def test_role_workspace_routes(self):
        from app.web_gateway.routing import ROLE_WORKSPACE_ROUTES, workspace_path_for_role

        self.assertEqual(workspace_path_for_role("SUPER_ADMIN"), "/app/admin")
        self.assertEqual(workspace_path_for_role("DOCTOR"), "/app/doctor")
        self.assertEqual(workspace_path_for_role("UNKNOWN"), "/app")
        self.assertIn("PATIENT", ROLE_WORKSPACE_ROUTES)

    def test_domain_config_defaults(self):
        from app import create_app

        app = create_app()
        app.config["TESTING"] = True
        with app.app_context():
            from app.web_gateway.config import api_base_url, public_site_url, web_app_url

            self.assertIn("dxcon.com.vn", public_site_url())
            self.assertIn("app.", web_app_url())
            self.assertIn("api.", api_base_url())

    def test_login_redirects_authenticated_user(self):
        from app import create_app
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User

        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()
        with app.app_context():
            db.create_all()
            user = User(
                email="gw@dxcon.test",
                role="RECEPTION",
                password_hash=hash_password("DemoPass123!"),
                is_active=True,
            )
            db.session.add(user)
            db.session.commit()
            with client.session_transaction() as sess:
                sess["user_id"] = user.id
                sess["role"] = user.role
                sess["email"] = user.email
            resp = client.get("/login", follow_redirects=False)
            self.assertIn(resp.status_code, {302, 303, 307, 308})
            self.assertIn("/app/reception", resp.headers.get("Location", ""))


if __name__ == "__main__":
    unittest.main()
