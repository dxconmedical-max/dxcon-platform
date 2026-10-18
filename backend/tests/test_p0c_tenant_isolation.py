"""P0-C: Mandatory tenant / membership isolation regression tests."""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_p0c_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from flask_jwt_extended import create_access_token

from app import create_app
from app.core.authenticated_identity import AuthenticatedIdentity, bind_authenticated_identity
from app.core.passwords import hash_password
from app.core.tenant_authorization import (
    AuthorizedTenant,
    authorize_clinic_id,
    authorize_doctor_id,
    authorize_partner_record,
    resolve_authorized_tenant,
    scoped_partner_ids,
)
from app.extensions.db import db
from app.models.clinic_profile import ClinicProfile
from app.models.doctor_profile import DoctorProfile
from app.models.invoice import Invoice
from app.models.lab_result import LabResult
from app.models.order import Order
from app.models.partner_foundation import (
    ORG_STATUS_ACTIVE,
    OrganizationUser,
    PartnerOrganization,
)
from app.models.sample_collection import SampleCollection
from app.models.user import User


class TenantIsolationP0CTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["API_AUTH_GATE_ENABLED"] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()

        self.org_a = PartnerOrganization(
            organization_code=f"P0CA-{uuid.uuid4().hex[:6].upper()}",
            organization_name="Tenant A Clinic Org",
            organization_type="CLINIC",
            status=ORG_STATUS_ACTIVE,
        )
        self.org_b = PartnerOrganization(
            organization_code=f"P0CB-{uuid.uuid4().hex[:6].upper()}",
            organization_name="Tenant B Clinic Org",
            organization_type="CLINIC",
            status=ORG_STATUS_ACTIVE,
        )
        db.session.add_all([self.org_a, self.org_b])
        db.session.flush()

        self.user_a = User(
            email=f"p0c-a-{uuid.uuid4().hex[:6]}@test.local",
            role="RECEPTION",
            password_hash=hash_password("Password123!"),
            is_active=True,
            organization_id=self.org_a.id,
        )
        self.user_b = User(
            email=f"p0c-b-{uuid.uuid4().hex[:6]}@test.local",
            role="RECEPTION",
            password_hash=hash_password("Password123!"),
            is_active=True,
            organization_id=self.org_b.id,
        )
        self.user_none = User(
            email=f"p0c-none-{uuid.uuid4().hex[:6]}@test.local",
            role="DOCTOR",
            password_hash=hash_password("Password123!"),
            is_active=True,
        )
        self.user_disabled = User(
            email=f"p0c-dis-{uuid.uuid4().hex[:6]}@test.local",
            role="ADMIN",
            password_hash=hash_password("Password123!"),
            is_active=True,
            organization_id=self.org_a.id,
        )
        self.admin = User(
            email=f"p0c-admin-{uuid.uuid4().hex[:6]}@test.local",
            role="ADMIN",
            password_hash=hash_password("Password123!"),
            is_active=True,
            organization_id=self.org_a.id,
        )
        self.super_admin = User(
            email=f"p0c-sa-{uuid.uuid4().hex[:6]}@test.local",
            role="SUPER_ADMIN",
            password_hash=hash_password("Password123!"),
            is_active=True,
        )
        self.doctor_a = User(
            email=f"p0c-doc-a-{uuid.uuid4().hex[:6]}@test.local",
            role="DOCTOR",
            password_hash=hash_password("Password123!"),
            is_active=True,
            organization_id=self.org_a.id,
        )
        self.lab_a = User(
            email=f"p0c-lab-a-{uuid.uuid4().hex[:6]}@test.local",
            role="LAB",
            password_hash=hash_password("Password123!"),
            is_active=True,
            organization_id=self.org_a.id,
        )
        db.session.add_all(
            [
                self.user_a,
                self.user_b,
                self.user_none,
                self.user_disabled,
                self.admin,
                self.super_admin,
                self.doctor_a,
                self.lab_a,
            ]
        )
        db.session.flush()

        db.session.add_all(
            [
                OrganizationUser(
                    organization_id=self.org_a.id,
                    user_id=self.user_a.id,
                    role_code="RECEPTION",
                    active=True,
                ),
                OrganizationUser(
                    organization_id=self.org_b.id,
                    user_id=self.user_b.id,
                    role_code="RECEPTION",
                    active=True,
                ),
                OrganizationUser(
                    organization_id=self.org_a.id,
                    user_id=self.user_disabled.id,
                    role_code="CLINIC_ADMIN",
                    active=False,
                ),
                OrganizationUser(
                    organization_id=self.org_a.id,
                    user_id=self.admin.id,
                    role_code="ORG_OWNER",
                    active=True,
                ),
                OrganizationUser(
                    organization_id=self.org_a.id,
                    user_id=self.doctor_a.id,
                    role_code="DOCTOR",
                    active=True,
                ),
                OrganizationUser(
                    organization_id=self.org_a.id,
                    user_id=self.lab_a.id,
                    role_code="VIEWER",
                    active=True,
                ),
            ]
        )

        self.clinic_a_id = f"clinic-a-{uuid.uuid4().hex[:8]}"
        self.clinic_b_id = f"clinic-b-{uuid.uuid4().hex[:8]}"
        db.session.add_all(
            [
                ClinicProfile(
                    clinic_id=self.clinic_a_id,
                    clinic_code=f"CA-{uuid.uuid4().hex[:6].upper()}",
                    name="Clinic A",
                    partner_id=self.org_a.id,
                ),
                ClinicProfile(
                    clinic_id=self.clinic_b_id,
                    clinic_code=f"CB-{uuid.uuid4().hex[:6].upper()}",
                    name="Clinic B",
                    partner_id=self.org_b.id,
                ),
            ]
        )

        self.doc_a_id = f"doc-a-{uuid.uuid4().hex[:8]}"
        self.doc_b_id = f"doc-b-{uuid.uuid4().hex[:8]}"
        db.session.add_all(
            [
                DoctorProfile(
                    doctor_id=self.doc_a_id,
                    doctor_code=f"DA-{uuid.uuid4().hex[:6].upper()}",
                    full_name="Doctor A",
                    email=self.doctor_a.email,
                ),
                DoctorProfile(
                    doctor_id=self.doc_b_id,
                    doctor_code=f"DB-{uuid.uuid4().hex[:6].upper()}",
                    full_name="Doctor B",
                    email=f"other-doc-{uuid.uuid4().hex[:6]}@test.local",
                ),
            ]
        )

        self.order_a = Order(
            order_code=f"ORD-A-{uuid.uuid4().hex[:6]}",
            patient_id=f"pat-a-{uuid.uuid4().hex[:6]}",
            laboratory_id=self.org_a.id,
            status="CREATED",
        )
        self.order_b = Order(
            order_code=f"ORD-B-{uuid.uuid4().hex[:6]}",
            patient_id=f"pat-b-{uuid.uuid4().hex[:6]}",
            laboratory_id=self.org_b.id,
            status="CREATED",
        )
        db.session.add_all([self.order_a, self.order_b])
        db.session.flush()

        self.collection_a = SampleCollection(
            order_id=self.order_a.id,
            partner_id=self.org_a.id,
            status="REQUESTED",
            collection_mode="HOME_COLLECTION",
        )
        self.collection_b = SampleCollection(
            order_id=self.order_b.id,
            partner_id=self.org_b.id,
            status="REQUESTED",
            collection_mode="HOME_COLLECTION",
        )
        db.session.add_all([self.collection_a, self.collection_b])

        self.result_a = LabResult(
            result_code=f"RES-A-{uuid.uuid4().hex[:6]}",
            medical_order_id=str(uuid.uuid4()),
            partner_id=self.org_a.id,
            status="PENDING",
        )
        self.result_b = LabResult(
            result_code=f"RES-B-{uuid.uuid4().hex[:6]}",
            medical_order_id=str(uuid.uuid4()),
            partner_id=self.org_b.id,
            status="PENDING",
        )
        db.session.add_all([self.result_a, self.result_b])

        self.invoice_a = Invoice(
            invoice_no=f"INV-A-{uuid.uuid4().hex[:6]}",
            company_id=self.org_a.id,
            order_id=self.order_a.id,
            medical_order_id=str(uuid.uuid4()),
            partner_id=self.org_a.id,
            total_amount=100,
        )
        self.invoice_b = Invoice(
            invoice_no=f"INV-B-{uuid.uuid4().hex[:6]}",
            company_id=self.org_b.id,
            order_id=self.order_b.id,
            medical_order_id=str(uuid.uuid4()),
            partner_id=self.org_b.id,
            total_amount=200,
        )
        db.session.add_all([self.invoice_a, self.invoice_b])
        db.session.commit()

        for user in (
            self.user_a,
            self.user_b,
            self.user_none,
            self.user_disabled,
            self.admin,
            self.super_admin,
            self.doctor_a,
            self.lab_a,
        ):
            user.token = create_access_token(
                identity=user.id,
                additional_claims={"role": user.role, "email": user.email},
            )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _auth(self, user, **extra):
        headers = {"Authorization": f"Bearer {user.token}"}
        headers.update(extra)
        return headers

    # --- Core tenant resolution ---

    def test_01_user_a_tenant_a_allowed(self):
        with self.app.test_request_context(
            "/api/v1/billing/invoices",
            headers=self._auth(self.user_a, **{"X-Organization-ID": self.org_a.id}),
        ):
            tenant = resolve_authorized_tenant(require_scope=True)
            self.assertIsInstance(tenant, AuthorizedTenant)
            self.assertEqual(tenant.organization_id, self.org_a.id)
            self.assertFalse(tenant.is_global_scope)

    def test_02_user_a_tenant_b_denied(self):
        with self.app.test_request_context(
            "/api/v1/billing/invoices",
            headers=self._auth(self.user_a, **{"X-Organization-ID": self.org_b.id}),
        ):
            result = resolve_authorized_tenant(require_scope=True)
            self.assertIsInstance(result, tuple)
            self.assertEqual(result[1], 403)

    def test_03_no_membership_denied(self):
        with self.app.test_request_context(
            "/api/v1/billing/invoices",
            headers=self._auth(self.user_none),
        ):
            result = resolve_authorized_tenant(require_scope=True)
            self.assertIsInstance(result, tuple)
            self.assertEqual(result[1], 403)

    def test_04_disabled_membership_denied(self):
        with self.app.test_request_context(
            "/api/v1/billing/invoices",
            headers=self._auth(self.user_disabled, **{"X-Organization-ID": self.org_a.id}),
        ):
            result = resolve_authorized_tenant(require_scope=True)
            self.assertIsInstance(result, tuple)
            self.assertEqual(result[1], 403)

    def test_05_spoof_x_clinic_id_denied(self):
        with self.app.test_request_context(
            f"/api/v1/clinic/dashboard?clinic_id={self.clinic_b_id}",
            headers=self._auth(self.user_a, **{"X-Clinic-Id": self.clinic_b_id}),
        ):
            bind_authenticated_identity()
            result = authorize_clinic_id(self.clinic_b_id)
            self.assertIsInstance(result, tuple)
            self.assertIn(result[1], {403, 404})

    def test_06_spoof_organization_id_denied(self):
        resp = self.client.get(
            "/api/v1/billing/invoices",
            headers=self._auth(self.user_a, **{"X-Organization-ID": self.org_b.id}),
        )
        self.assertEqual(resp.status_code, 403)

    def test_07_spoof_x_doctor_id_denied(self):
        with self.app.test_request_context(
            f"/api/v1/doctor/dashboard?doctor_id={self.doc_b_id}",
            headers=self._auth(self.doctor_a, **{"X-Doctor-Id": self.doc_b_id}),
        ):
            bind_authenticated_identity()
            result = authorize_doctor_id(self.doc_b_id)
            self.assertIsInstance(result, tuple)
            self.assertIn(result[1], {403, 404})

    def test_08_doctor_a_cannot_use_doctor_b(self):
        resp = self.client.get(
            f"/api/v1/doctor/dashboard?doctor_id={self.doc_b_id}",
            headers=self._auth(self.doctor_a),
        )
        self.assertIn(resp.status_code, {403, 404})

    def test_09_lab_a_cannot_see_lab_b_results(self):
        resp = self.client.get(
            f"/api/v1/results/{self.result_b.id}",
            headers=self._auth(self.lab_a),
        )
        self.assertIn(resp.status_code, {403, 404})

    def test_10_clinic_a_cannot_open_clinic_b(self):
        resp = self.client.get(
            f"/api/v1/clinic/dashboard?clinic_id={self.clinic_b_id}",
            headers=self._auth(self.user_a, **{"X-Clinic-Id": self.clinic_b_id}),
        )
        self.assertIn(resp.status_code, {403, 404})

    def test_11_cross_tenant_order_denied(self):
        resp = self.client.get(
            f"/api/v1/order-lifecycle/orders/{self.order_b.id}",
            headers=self._auth(self.user_a),
        )
        self.assertIn(resp.status_code, {403, 404})

    def test_12_cross_tenant_sample_collection_denied(self):
        resp = self.client.get(
            f"/api/v1/sample-collections/{self.collection_b.id}",
            headers=self._auth(self.user_a),
        )
        self.assertIn(resp.status_code, {403, 404})

    def test_13_cross_tenant_result_denied(self):
        resp = self.client.get(
            f"/api/v1/results/{self.result_b.id}",
            headers=self._auth(self.user_a),
        )
        self.assertIn(resp.status_code, {403, 404})

    def test_14_cross_tenant_invoice_mutation_denied(self):
        resp = self.client.post(
            f"/api/v1/billing/invoices/{self.invoice_b.id}/mark-paid",
            headers=self._auth(self.user_a, **{"Content-Type": "application/json"}),
            json={"amount": 1},
        )
        self.assertIn(resp.status_code, {403, 404})

    def test_15_super_admin_global_scope(self):
        with self.app.test_request_context(
            "/api/v1/billing/invoices",
            headers=self._auth(self.super_admin),
        ):
            tenant = resolve_authorized_tenant(require_scope=True)
            self.assertIsInstance(tenant, AuthorizedTenant)
            self.assertTrue(tenant.is_global_scope)
            self.assertIsNone(scoped_partner_ids(tenant))

    def test_16_admin_cannot_auto_cross_tenants(self):
        # ADMIN in org A cannot select org B
        with self.app.test_request_context(
            "/api/v1/billing/invoices",
            headers=self._auth(self.admin, **{"X-Organization-ID": self.org_b.id}),
        ):
            result = resolve_authorized_tenant(require_scope=True)
            self.assertIsInstance(result, tuple)
            self.assertEqual(result[1], 403)

        # ADMIN listing without spoof sees only org A invoices
        resp = self.client.get(
            "/api/v1/billing/invoices",
            headers=self._auth(self.admin),
        )
        self.assertEqual(resp.status_code, 200)
        invoices = resp.get_json()
        rows = invoices.get("invoices", []) if isinstance(invoices, dict) else invoices
        partner_ids = {i.get("partner_id") for i in rows}
        self.assertNotIn(self.org_b.id, partner_ids)

    def test_17_no_valid_scope_fails_closed(self):
        resp = self.client.get(
            "/api/v1/billing/invoices",
            headers=self._auth(self.user_none),
        )
        self.assertEqual(resp.status_code, 403)

    def test_18_missing_organization_id_does_not_mean_all_orgs(self):
        """Regression: omit organization_id → membership preferred org, never all tenants."""
        with self.app.test_request_context(
            "/api/v1/billing/invoices",
            headers=self._auth(self.user_a),
        ):
            tenant = resolve_authorized_tenant(require_scope=True)
            self.assertIsInstance(tenant, AuthorizedTenant)
            self.assertFalse(tenant.is_global_scope)
            ids = scoped_partner_ids(tenant)
            self.assertIsNotNone(ids)
            self.assertIn(self.org_a.id, ids)
            self.assertNotIn(self.org_b.id, ids)

        resp = self.client.get(
            "/api/v1/billing/invoices",
            headers=self._auth(self.user_a),
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        rows = payload.get("invoices", []) if isinstance(payload, dict) else payload
        for row in rows:
            self.assertEqual(row.get("partner_id"), self.org_a.id)

    def test_19_audit_actor_authenticated(self):
        from app.core.authenticated_identity import authenticated_actor_email

        with self.app.test_request_context(
            "/api/v1/billing/invoices",
            headers=self._auth(
                self.user_a,
                **{"X-User-Email": "spoof@evil.local", "X-Organization-ID": self.org_a.id},
            ),
        ):
            identity = bind_authenticated_identity()
            self.assertIsInstance(identity, AuthenticatedIdentity)
            self.assertEqual(authenticated_actor_email(), self.user_a.email)

    def test_clinic_a_allowed(self):
        with self.app.test_request_context(
            f"/api/v1/clinic/dashboard?clinic_id={self.clinic_a_id}",
            headers=self._auth(self.user_a),
        ):
            bind_authenticated_identity()
            result = authorize_clinic_id(self.clinic_a_id)
            self.assertEqual(result, self.clinic_a_id)

    def test_own_result_allowed(self):
        with self.app.test_request_context(
            f"/api/v1/results/{self.result_a.id}",
            headers=self._auth(self.lab_a),
        ):
            bind_authenticated_identity()
            tenant = authorize_partner_record(self.result_a.partner_id)
            self.assertIsInstance(tenant, AuthorizedTenant)

    def test_own_order_list_scoped(self):
        resp = self.client.get(
            "/api/v1/order-lifecycle/orders",
            headers=self._auth(self.user_a),
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        for order in body.get("orders", []):
            self.assertEqual(order.get("laboratory_id"), self.org_a.id)

    def test_results_list_scoped(self):
        resp = self.client.get(
            "/api/v1/results",
            headers=self._auth(self.lab_a),
        )
        self.assertEqual(resp.status_code, 200)
        for row in resp.get_json().get("results", []):
            self.assertEqual(row.get("partner_id"), self.org_a.id)


if __name__ == "__main__":
    unittest.main()
