"""P0-B: Role authorization / admin authorization regression tests."""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_p0b_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from flask_jwt_extended import create_access_token

from app import create_app
from app.core.audit import write_audit
from app.core.authenticated_identity import (
    AuthenticatedIdentity,
    authenticated_actor_email,
    bind_authenticated_identity,
)
from app.core.authz import (
    identity_has_org_role,
    identity_has_permission,
    identity_has_platform_role,
    require_org_role,
    require_permission,
    require_platform_role,
)
from app.core.passwords import hash_password
from app.extensions.db import db
from app.models.audit_log import AuditLog
from app.models.partner_foundation import (
    ORG_STATUS_ACTIVE,
    OrganizationUser,
    PartnerOrganization,
)
from app.models.user import User


class AuthorizationP0BTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["API_AUTH_GATE_ENABLED"] = False

        @cls.app.get("/__p0b__/org-owner-only")
        @require_org_role("ORG_OWNER", "CLINIC_ADMIN")
        def _p0b_org_owner_only():
            return {"ok": True}, 200

        @cls.app.get("/__p0b__/perm-org-create")
        @require_permission("org.create")
        def _p0b_perm_org_create():
            return {"ok": True}, 200

        @cls.app.get("/__p0b__/platform-admin")
        @require_platform_role("ADMIN", "SUPER_ADMIN")
        def _p0b_platform_admin():
            return {"ok": True}, 200

    def setUp(self):
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()

        self.users = {}
        for role in (
            "PATIENT",
            "DOCTOR",
            "RECEPTION",
            "ADMIN",
            "SUPER_ADMIN",
            "COLLECTOR",
        ):
            user = User(
                email=f"p0b-{role.lower()}-{uuid.uuid4().hex[:6]}@test.local",
                role=role,
                password_hash=hash_password("Password123!"),
                is_active=True,
            )
            db.session.add(user)
            self.users[role] = user

        self.org = PartnerOrganization(
            organization_code=f"P0B-{uuid.uuid4().hex[:6].upper()}",
            organization_name="P0-B Test Org",
            organization_type="CLINIC",
            status=ORG_STATUS_ACTIVE,
        )
        db.session.add(self.org)
        db.session.flush()

        self.membership_owner = OrganizationUser(
            organization_id=self.org.id,
            user_id=self.users["DOCTOR"].id,
            role_code="ORG_OWNER",
            active=True,
        )
        self.membership_viewer = OrganizationUser(
            organization_id=self.org.id,
            user_id=self.users["PATIENT"].id,
            role_code="VIEWER",
            active=True,
        )
        self.users["DOCTOR"].organization_id = self.org.id
        self.users["PATIENT"].organization_id = self.org.id
        db.session.add_all([self.membership_owner, self.membership_viewer])
        db.session.commit()

        for role, user in self.users.items():
            user.token = create_access_token(
                identity=user.id,
                additional_claims={"role": role, "email": user.email},
            )

        self.spoof_token = create_access_token(
            identity=self.users["PATIENT"].id,
            additional_claims={
                "role": "ADMIN",
                "email": self.users["PATIENT"].email,
                "is_admin": True,
            },
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _auth(self, role: str | None = None, token: str | None = None, **extra_headers):
        headers = dict(extra_headers)
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        elif role is not None:
            headers["Authorization"] = f"Bearer {self.users[role].token}"
        return headers

    def test_01_anonymous_admin_users_401(self):
        resp = self.client.get("/api/v1/admin/users")
        self.assertEqual(resp.status_code, 401)

    def test_02_patient_admin_users_403(self):
        resp = self.client.get("/api/v1/admin/users", headers=self._auth("PATIENT"))
        self.assertEqual(resp.status_code, 403)

    def test_03_doctor_admin_users_403(self):
        resp = self.client.get("/api/v1/admin/users", headers=self._auth("DOCTOR"))
        self.assertEqual(resp.status_code, 403)

    def test_04_reception_admin_users_403(self):
        resp = self.client.get("/api/v1/admin/users", headers=self._auth("RECEPTION"))
        self.assertEqual(resp.status_code, 403)

    def test_05_admin_admin_users_200(self):
        resp = self.client.get("/api/v1/admin/users", headers=self._auth("ADMIN"))
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(resp.get_json().get("count", 0), 1)

    def test_06_super_admin_admin_users_200(self):
        resp = self.client.get("/api/v1/admin/users", headers=self._auth("SUPER_ADMIN"))
        self.assertEqual(resp.status_code, 200)

    def test_07_spoof_x_user_role_admin_still_403(self):
        resp = self.client.get(
            "/api/v1/admin/users",
            headers=self._auth("PATIENT", **{"X-User-Role": "ADMIN"}),
        )
        self.assertEqual(resp.status_code, 403)

    def test_08_spoof_x_role_admin_still_403(self):
        resp = self.client.get(
            "/api/v1/admin/users",
            headers=self._auth("DOCTOR", **{"X-Role": "ADMIN"}),
        )
        self.assertEqual(resp.status_code, 403)

    def test_09_body_role_admin_still_403(self):
        resp = self.client.get(
            "/api/v1/admin/users",
            headers=self._auth("RECEPTION", **{"Content-Type": "application/json"}),
            json={"role": "ADMIN", "is_admin": True, "admin": True},
        )
        self.assertEqual(resp.status_code, 403)

    def test_10_query_role_admin_still_403(self):
        resp = self.client.get(
            "/api/v1/admin/users?role=ADMIN&is_admin=true&admin=true",
            headers=self._auth("PATIENT"),
        )
        self.assertEqual(resp.status_code, 403)

    def test_spoofed_jwt_role_claim_cannot_elevate(self):
        with self.app.test_request_context(
            "/api/v1/admin/users",
            headers=self._auth(token=self.spoof_token, **{"X-User-Role": "SUPER_ADMIN"}),
        ):
            result = bind_authenticated_identity()
            self.assertIsInstance(result, AuthenticatedIdentity)
            self.assertEqual(result.platform_role, "PATIENT")
            self.assertFalse(identity_has_platform_role(result, "ADMIN", "SUPER_ADMIN"))

        resp = self.client.get(
            "/api/v1/admin/users",
            headers=self._auth(token=self.spoof_token, **{"X-User-Role": "ADMIN"}),
        )
        self.assertEqual(resp.status_code, 403)

    def test_11_org_owner_membership_allows_org_role_route(self):
        resp = self.client.get(
            "/__p0b__/org-owner-only",
            headers=self._auth("DOCTOR"),
        )
        self.assertEqual(resp.status_code, 200)

        resp2 = self.client.get(
            "/__p0b__/perm-org-create",
            headers=self._auth("DOCTOR"),
        )
        self.assertEqual(resp2.status_code, 200)

    def test_12_viewer_membership_denied_org_owner_route(self):
        resp = self.client.get(
            "/__p0b__/org-owner-only",
            headers=self._auth("PATIENT"),
        )
        self.assertEqual(resp.status_code, 403)

        resp2 = self.client.get(
            "/__p0b__/perm-org-create",
            headers=self._auth("PATIENT"),
        )
        self.assertEqual(resp2.status_code, 403)

    def test_org_role_helpers_use_server_membership(self):
        with self.app.test_request_context(
            "/__p0b__/org-owner-only",
            headers=self._auth("DOCTOR", **{"X-User-Role": "VIEWER"}),
        ):
            identity = bind_authenticated_identity()
            self.assertIsInstance(identity, AuthenticatedIdentity)
            self.assertEqual(identity.organization_role, "ORG_OWNER")
            self.assertTrue(identity_has_org_role(identity, "ORG_OWNER"))
            self.assertTrue(identity_has_permission(identity, "org.create"))

        with self.app.test_request_context(
            "/__p0b__/org-owner-only",
            headers=self._auth("PATIENT"),
        ):
            identity = bind_authenticated_identity()
            self.assertIsInstance(identity, AuthenticatedIdentity)
            self.assertEqual(identity.organization_role, "VIEWER")
            self.assertFalse(identity_has_org_role(identity, "ORG_OWNER"))

    def test_13_audit_actor_equals_authenticated_user(self):
        admin = self.users["ADMIN"]
        with self.app.test_request_context(
            "/api/v1/security/users",
            method="POST",
            headers=self._auth(
                "ADMIN",
                **{
                    "X-User-Email": "spoofed@evil.local",
                    "X-User-Role": "SUPER_ADMIN",
                    "Content-Type": "application/json",
                },
            ),
            json={
                "email": f"created-{uuid.uuid4().hex[:6]}@test.local",
                "password": "Password123!",
            },
        ):
            result = bind_authenticated_identity()
            self.assertIsInstance(result, AuthenticatedIdentity)
            actor = authenticated_actor_email()
            self.assertEqual(actor, admin.email)
            self.assertNotEqual(actor, "spoofed@evil.local")
            write_audit(
                action="P0B_TEST_AUDIT",
                object_type="TEST",
                object_id="1",
                user_email=actor,
            )
            db.session.commit()

        row = (
            AuditLog.query.filter_by(action="P0B_TEST_AUDIT")
            .order_by(AuditLog.created_at.desc())
            .first()
        )
        self.assertIsNotNone(row)
        self.assertEqual(row.user_email, admin.email)

    def test_security_create_user_audit_uses_authenticated_admin(self):
        admin = self.users["ADMIN"]
        email = f"sec-create-{uuid.uuid4().hex[:6]}@test.local"
        resp = self.client.post(
            "/api/v1/security/users",
            headers=self._auth(
                "ADMIN",
                **{
                    "X-User-Email": "attacker@evil.local",
                    "Content-Type": "application/json",
                },
            ),
            json={"email": email, "password": "Password123!", "role": "PATIENT"},
        )
        self.assertEqual(resp.status_code, 201, resp.get_json())
        row = (
            AuditLog.query.filter_by(action="CREATE_USER")
            .order_by(AuditLog.created_at.desc())
            .first()
        )
        self.assertIsNotNone(row)
        self.assertEqual(row.user_email, admin.email)
        self.assertNotEqual(row.user_email, "attacker@evil.local")
        self.assertNotEqual(row.user_email, "ADMIN")

    def test_14_authorized_admin_security_users_ok(self):
        resp = self.client.get("/api/v1/security/users", headers=self._auth("ADMIN"))
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(resp.get_json().get("count", 0), 1)

    def test_15_public_endpoints_still_work(self):
        health = self.client.get("/api/v1/system/health")
        self.assertIn(health.status_code, {200, 503})

        login = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": self.users["DOCTOR"].email,
                "password": "Password123!",
            },
        )
        self.assertEqual(login.status_code, 200, login.get_json())
        self.assertIn("access_token", login.get_json())

    def test_role_dashboard_patient_cannot_open_admin_even_with_spoof(self):
        resp = self.client.get(
            "/api/v1/role-dashboards/admin?role=ADMIN",
            headers=self._auth("PATIENT", **{"X-User-Role": "ADMIN"}),
        )
        self.assertEqual(resp.status_code, 403)

    def test_role_dashboard_admin_can_open_admin(self):
        resp = self.client.get(
            "/api/v1/role-dashboards/admin",
            headers=self._auth("ADMIN"),
        )
        self.assertEqual(resp.status_code, 200, resp.get_json())
        self.assertTrue(resp.get_json().get("success"))

    def test_anonymous_role_dashboard_401(self):
        resp = self.client.get(
            "/api/v1/role-dashboards/admin",
            headers={"X-User-Role": "ADMIN"},
        )
        self.assertEqual(resp.status_code, 401)

    def test_require_platform_role_decorator(self):
        resp = self.client.get("/__p0b__/platform-admin", headers=self._auth("ADMIN"))
        self.assertEqual(resp.status_code, 200)
        denied = self.client.get("/__p0b__/platform-admin", headers=self._auth("DOCTOR"))
        self.assertEqual(denied.status_code, 403)


if __name__ == "__main__":
    unittest.main()
