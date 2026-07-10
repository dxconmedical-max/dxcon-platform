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
from app.models.partner_foundation import OrganizationUser, PartnerOrganization
from app.models.user import User
from app.partner_foundation.service import ensure_default_organization, seed_organization_roles


class AuthContextApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        ensure_default_organization()
        seed_organization_roles()

        self.user = User(
            email="auth-context@dxcon.test",
            role="DOCTOR",
            password_hash=hash_password("DemoPass123!"),
            is_active=True,
        )
        db.session.add(self.user)
        db.session.flush()

        self.org_a = PartnerOrganization(
            organization_code="CLINIC_A",
            organization_name="Clinic A",
            organization_type="CLINIC",
            status="active",
        )
        self.org_b = PartnerOrganization(
            organization_code="CLINIC_B",
            organization_name="Clinic B",
            organization_type="CLINIC",
            status="suspended",
        )
        db.session.add_all([self.org_a, self.org_b])
        db.session.flush()

        db.session.add(
            OrganizationUser(
                organization_id=self.org_a.id,
                user_id=self.user.id,
                role_code="DOCTOR",
                active=True,
            )
        )
        db.session.add(
            OrganizationUser(
                organization_id=self.org_b.id,
                user_id=self.user.id,
                role_code="VIEWER",
                active=True,
            )
        )
        self.user.organization_id = self.org_a.id
        db.session.commit()

        login = self.client.post(
            "/api/v1/auth/login",
            json={"email": self.user.email, "password": "DemoPass123!"},
        )
        self.assertEqual(login.status_code, 200)
        payload = login.get_json()
        self.access_token = payload["access_token"]

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}

    def test_auth_me(self):
        response = self.client.get("/api/v1/auth/me", headers=self._auth_headers())
        self.assertEqual(response.status_code, 200)
        data = response.get_json()["data"]
        self.assertEqual(data["user"]["email"], self.user.email)
        self.assertGreaterEqual(len(data["memberships"]), 1)

    def test_auth_memberships(self):
        response = self.client.get("/api/v1/auth/memberships", headers=self._auth_headers())
        self.assertEqual(response.status_code, 200)
        memberships = response.get_json()["data"]
        self.assertEqual(len(memberships), 2)

    def test_switch_organization(self):
        response = self.client.post(
            "/api/v1/auth/switch-organization",
            headers=self._auth_headers(),
            json={"organization_id": self.org_a.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["workspace"], "/app/doctor")

    def test_switch_suspended_organization_rejected(self):
        response = self.client.post(
            "/api/v1/auth/switch-organization",
            headers=self._auth_headers(),
            json={"organization_id": self.org_b.id},
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("suspended", response.get_json()["error"].lower())

    def test_capabilities(self):
        response = self.client.get("/api/v1/auth/capabilities", headers=self._auth_headers())
        self.assertEqual(response.status_code, 200)
        data = response.get_json()["data"]
        self.assertIn("permissions", data)
        self.assertIn("features", data)
        self.assertEqual(data["workspace"], "/app/doctor")

    def test_forgot_password(self):
        response = self.client.post(
            "/api/v1/auth/forgot-password",
            json={"email": self.user.email},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])

    def test_reset_password_not_enabled(self):
        response = self.client.post(
            "/api/v1/auth/reset-password",
            json={"token": "abc", "password": "NewPass123!"},
        )
        self.assertEqual(response.status_code, 501)


if __name__ == "__main__":
    unittest.main()
