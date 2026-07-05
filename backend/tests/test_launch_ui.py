import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.passwords import hash_password
from app.extensions.db import db
from app.models.user import User


class LaunchUiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        db.session.add(
            User(
                email="launch-ui-admin@demo.dxcon.test",
                role="ADMIN",
                password_hash=hash_password("DemoPass123!"),
                is_active=True,
            )
        )
        db.session.commit()
        with self.client.session_transaction() as sess:
            user = User.query.filter_by(email="launch-ui-admin@demo.dxcon.test").first()
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["email"] = user.email

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_root_redirects_to_login(self):
        response = self.client.get("/", follow_redirects=False)
        self.assertIn(response.status_code, {302, 303, 307, 308})
        self.assertIn("/login", response.headers.get("Location", ""))

    def test_public_marketing_home(self):
        response = self.client.get("/home")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("launch-marketing-hero", body)
        self.assertIn("DxCon", body)
        self.assertIn("css/dxcon.css", body)

    def test_login_page_shell(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("launch-login-card", body)
        self.assertIn("Sign in", body)
        self.assertIn("css/dxcon.css", body)

    def test_static_stylesheet_served(self):
        response = self.client.get("/static/css/dxcon.css")
        self.assertEqual(response.status_code, 200)
        self.assertIn(".launch-login-wrap", response.get_data(as_text=True))

    def test_role_dashboards(self):
        routes = (
            "/app/executive",
            "/app/reception",
            "/app/doctor",
            "/app/lab",
            "/app/collector",
            "/app/patient",
            "/app/system",
            "/executive-v10",
        )
        for path in routes:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            body = response.get_data(as_text=True)
            self.assertIn("launch-shell", body, path)
            self.assertIn("css/dxcon.css", body, path)

    def test_health_probes(self):
        for path in ("/health", "/ready"):
            response = self.client.get(path)
            self.assertIn(response.status_code, {200, 503}, path)


if __name__ == "__main__":
    unittest.main()
