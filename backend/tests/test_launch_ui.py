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
from app.web.launch_ui_modules import MODULE_ROUTES


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
        self.assertIn("/login/demo?role=", body)

    def test_demo_role_entry_routes(self):
        cases = (
            ("ADMIN", "/app/executive"),
            ("DOCTOR", "/app/doctor"),
            ("LAB", "/app/lab"),
            ("RECEPTION", "/app/reception"),
            ("COLLECTOR", "/app/collector"),
            ("PATIENT", "/app/patient"),
        )
        for role, target in cases:
            with self.client.session_transaction() as sess:
                sess.clear()
            response = self.client.get(f"/login/demo?role={role}", follow_redirects=False)
            self.assertIn(response.status_code, {302, 303, 307, 308}, role)
            self.assertIn(target, response.headers.get("Location", ""), role)

    def test_static_stylesheet_served(self):
        response = self.client.get("/static/css/dxcon.css")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn(".launch-login-wrap", body)
        self.assertIn(".launch-action-card", body)

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
            self.assertIn("launch-action-card", body, path)

    def test_module_pages(self):
        for path in MODULE_ROUTES:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            body = response.get_data(as_text=True)
            self.assertIn("launch-shell", body, path)
            self.assertIn("css/dxcon.css", body, path)

    def test_detail_pages(self):
        from app.web.launch_ui_data import get_sample_order_key, get_sample_patient_key, get_sample_report_key

        for path in (
            f"/app/patients/{get_sample_patient_key()}",
            f"/app/orders/{get_sample_order_key()}",
            f"/app/reports/{get_sample_report_key()}",
        ):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertIn("launch-shell", response.get_data(as_text=True), path)

    def test_demo_data_helpers(self):
        from app.web.launch_ui_data import get_demo_counts, get_recent_orders, get_recent_patients

        counts = get_demo_counts()
        self.assertIn("patients", counts)
        self.assertIsInstance(get_recent_patients(), list)
        self.assertIsInstance(get_recent_orders(), list)

    def test_health_probes(self):
        for path in ("/health", "/ready"):
            response = self.client.get(path)
            self.assertIn(response.status_code, {200, 503}, path)


if __name__ == "__main__":
    unittest.main()
