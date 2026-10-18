"""P0-A: Authenticated identity foundation regression tests."""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_p0a_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from flask_jwt_extended import create_access_token, create_refresh_token

from app import create_app
from app.core.authenticated_identity import (
    AuthenticatedIdentity,
    bind_authenticated_identity,
    get_authenticated_identity,
    get_authenticated_user,
)
from app.core.passwords import hash_password
from app.extensions.db import db
from app.models.user import User


class AuthenticatedIdentityP0ATests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["API_AUTH_GATE_ENABLED"] = False  # exercise blueprint gate directly
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()

        self.user = User(
            email=f"p0a-{uuid.uuid4().hex[:8]}@test.local",
            role="DOCTOR",
            password_hash=hash_password("Password123!"),
            is_active=True,
        )
        self.other = User(
            email=f"other-{uuid.uuid4().hex[:8]}@test.local",
            role="PATIENT",
            password_hash=hash_password("Password123!"),
            is_active=True,
        )
        self.admin = User(
            email=f"admin-{uuid.uuid4().hex[:8]}@test.local",
            role="ADMIN",
            password_hash=hash_password("Password123!"),
            is_active=True,
        )
        db.session.add_all([self.user, self.other, self.admin])
        db.session.commit()
        self.user_id = self.user.id
        self.other_id = self.other.id
        self.admin_id = self.admin.id
        self.user_email = self.user.email
        self.other_email = self.other.email

        self.token = create_access_token(
            identity=self.user_id,
            additional_claims={"role": "DOCTOR", "email": self.user_email},
        )
        self.other_token = create_access_token(
            identity=self.other_id,
            additional_claims={"role": "PATIENT", "email": self.other_email},
        )
        self.admin_token = create_access_token(
            identity=self.admin_id,
            additional_claims={"role": "ADMIN", "email": self.admin.email},
        )
        self.refresh_token = create_refresh_token(
            identity=self.user_id,
            additional_claims={"role": "DOCTOR", "email": self.user_email},
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _auth(self, token=None):
        return {"Authorization": f"Bearer {token or self.token}"}

    # --- Core identity helper ---

    def test_no_auth_bind_returns_401(self):
        with self.app.test_request_context("/api/v1/clinic/dashboard"):
            result = bind_authenticated_identity()
            self.assertIsInstance(result, tuple)
            body, status = result
            self.assertEqual(status, 401)

    def test_valid_jwt_resolves_identity(self):
        with self.app.test_request_context(
            "/api/v1/clinic/dashboard",
            headers=self._auth(),
        ):
            result = bind_authenticated_identity()
            self.assertIsInstance(result, AuthenticatedIdentity)
            self.assertEqual(result.user_id, self.user_id)
            self.assertEqual(result.email, self.user_email)
            self.assertEqual(result.platform_role, "DOCTOR")
            self.assertEqual(result.auth_method, "jwt")
            self.assertEqual(get_authenticated_identity().user_id, self.user_id)
            self.assertEqual(get_authenticated_user().id, self.user_id)

    def test_invalid_jwt_returns_401(self):
        resp = self.client.get(
            "/api/v1/clinic/dashboard",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        self.assertEqual(resp.status_code, 401)

    def test_refresh_token_not_accepted_as_api_identity(self):
        resp = self.client.get(
            "/api/v1/clinic/dashboard",
            headers={"Authorization": f"Bearer {self.refresh_token}"},
        )
        self.assertEqual(resp.status_code, 401)

    def test_session_auth_resolves_identity(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user_id
            sess["role"] = "DOCTOR"
            sess["email"] = self.user_email
        resp = self.client.get("/api/v1/clinic/dashboard")
        # Authed but missing clinic_id → 400 (not 401)
        self.assertEqual(resp.status_code, 400)
        body = resp.get_json() or {}
        err = body.get("error", body)
        err_text = err if isinstance(err, str) else str(err)
        self.assertIn("clinic_id", err_text.lower())

    # --- Portal / clinical routes ---

    def test_clinic_dashboard_no_jwt_401(self):
        resp = self.client.get("/api/v1/clinic/dashboard?clinic_id=c1")
        self.assertEqual(resp.status_code, 401)

    def test_clinic_spoofed_email_without_jwt_still_401(self):
        resp = self.client.get(
            "/api/v1/clinic/dashboard?clinic_id=c1",
            headers={"X-User-Email": self.other_email, "X-Clinic-Id": "c1"},
        )
        self.assertEqual(resp.status_code, 401)

    def test_clinic_spoofed_email_with_jwt_keeps_jwt_user(self):
        captured = {}

        from app.api.clinic_portal import routes as clinic_routes

        original = clinic_routes._actor_email

        def _capture():
            email = original()
            captured["actor"] = email
            identity = get_authenticated_identity()
            captured["user_id"] = identity.user_id if identity else None
            return email

        clinic_routes._actor_email = _capture
        try:
            # Will 400/404 on missing clinic data, but actor must resolve first via before_request
            with self.app.test_request_context(
                "/api/v1/clinic/profile",
                method="PUT",
                headers={
                    **self._auth(),
                    "X-User-Email": self.other_email,
                    "X-Clinic-Id": "missing-clinic",
                    "Content-Type": "application/json",
                },
                json={"clinic_id": "missing-clinic", "name": "x"},
            ):
                result = bind_authenticated_identity()
                self.assertIsInstance(result, AuthenticatedIdentity)
                self.assertEqual(result.user_id, self.user_id)
                self.assertEqual(result.email, self.user_email)
                self.assertNotEqual(result.email, self.other_email)
                self.assertEqual(clinic_routes._actor_email(), self.user_email)
                self.assertEqual(captured["actor"], self.user_email)
                self.assertEqual(captured["user_id"], self.user_id)
        finally:
            clinic_routes._actor_email = original

    def test_client_user_id_header_cannot_override_jwt_user(self):
        with self.app.test_request_context(
            "/api/v1/doctor/dashboard",
            headers={
                **self._auth(),
                "X-User-Id": self.other_id,
                "X-User-Email": self.other_email,
                "X-Doctor-Id": "doc-1",
            },
        ):
            result = bind_authenticated_identity()
            self.assertIsInstance(result, AuthenticatedIdentity)
            self.assertEqual(result.user_id, self.user_id)
            self.assertNotEqual(result.user_id, self.other_id)

    def test_doctor_and_patient_portals_require_auth(self):
        self.assertEqual(self.client.get("/api/v1/doctor/dashboard?doctor_id=d1").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/patient/dashboard?patient_id=p1").status_code, 401)

    def test_billing_results_lab_order_lifecycle_require_auth(self):
        self.assertEqual(self.client.get("/api/v1/billing/invoices").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/results").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/lab/dashboard").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/order-lifecycle/orders").status_code, 401)

    def test_billing_with_valid_jwt_not_401(self):
        resp = self.client.get("/api/v1/billing/invoices", headers=self._auth())
        # Authenticated: must not be 401. Without membership, P0-C correctly returns 403.
        self.assertNotEqual(resp.status_code, 401)
        self.assertIn(resp.status_code, {200, 403})

    def test_admin_users_requires_admin_role(self):
        unauth = self.client.get("/api/v1/admin/users")
        self.assertEqual(unauth.status_code, 401)

        doctor = self.client.get("/api/v1/admin/users", headers=self._auth())
        self.assertEqual(doctor.status_code, 403)

        admin = self.client.get("/api/v1/admin/users", headers=self._auth(self.admin_token))
        self.assertEqual(admin.status_code, 200)
        self.assertGreaterEqual(admin.get_json().get("count", 0), 1)

    def test_public_auth_login_still_works(self):
        resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": self.user_email, "password": "Password123!"},
        )
        self.assertEqual(resp.status_code, 200, resp.get_json())
        self.assertIn("access_token", resp.get_json())

    def test_public_system_health_still_works(self):
        resp = self.client.get("/api/v1/system/health")
        self.assertIn(resp.status_code, {200, 503})


if __name__ == "__main__":
    unittest.main()
