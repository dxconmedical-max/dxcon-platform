"""P0-6: leftover anonymous write-surface hardening."""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_p06_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from flask_jwt_extended import create_access_token

from app import create_app
from app.core.passwords import hash_password
from app.core.statuses import (
    MAPPING_ACTIVE,
    PARTNER_ACTIVE,
    PAYMENT_GATEWAY_COMPLETED,
    PAYMENT_PROVIDER_STRIPE,
)
from app.extensions.db import db
from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.models.partner import Partner
from app.models.partner_foundation import (
    ORG_STATUS_ACTIVE,
    OrganizationUser,
    PartnerOrganization,
)
from app.models.partner_service_mapping import PartnerServiceMapping
from app.models.user import User
from app.services.slot_generation import SlotGenerationService


PASSWORD = "Password123!"


class AnonymousWriteSurfaceP06Tests(unittest.TestCase):
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
            organization_code=f"P06A-{uuid.uuid4().hex[:6].upper()}",
            organization_name="P06 Org A",
            organization_type="CLINIC",
            status=ORG_STATUS_ACTIVE,
        )
        self.org_b = PartnerOrganization(
            organization_code=f"P06B-{uuid.uuid4().hex[:6].upper()}",
            organization_name="P06 Org B",
            organization_type="CLINIC",
            status=ORG_STATUS_ACTIVE,
        )
        db.session.add_all([self.org_a, self.org_b])
        db.session.flush()

        self.admin = User(
            email=f"p06-admin-{uuid.uuid4().hex[:8]}@test.local",
            role="ADMIN",
            password_hash=hash_password(PASSWORD),
            is_active=True,
            organization_id=self.org_a.id,
        )
        self.other = User(
            email=f"p06-other-{uuid.uuid4().hex[:8]}@test.local",
            role="PATIENT",
            password_hash=hash_password(PASSWORD),
            is_active=True,
            organization_id=self.org_b.id,
        )
        db.session.add_all([self.admin, self.other])
        db.session.flush()
        db.session.add_all(
            [
                OrganizationUser(
                    organization_id=self.org_a.id,
                    user_id=self.admin.id,
                    role_code="ORG_OWNER",
                    active=True,
                ),
                OrganizationUser(
                    organization_id=self.org_b.id,
                    user_id=self.other.id,
                    role_code="VIEWER",
                    active=True,
                ),
            ]
        )

        db.session.add(Company(company_code="DX", company_name="DxCon", tax_code="01"))
        cat = DiagnosticCategory(category_code="BIO", name="Bio", is_active=True)
        db.session.add(cat)
        db.session.flush()
        svc = DiagnosticService(
            service_code="GLU", name="Glucose", category_id=cat.id, is_active=True
        )
        db.session.add(svc)
        self.partner = Partner(
            partner_code="PTR-P06",
            partner_type="LABORATORY",
            legal_name="P06 Lab",
            display_name="P06 Lab",
            status=PARTNER_ACTIVE,
        )
        db.session.add(self.partner)
        db.session.flush()
        self.mapping = PartnerServiceMapping(
            partner_id=self.partner.id,
            diagnostic_service_id=svc.id,
            partner_service_code="P06-GLU",
            partner_service_name="Glucose",
            price=150000,
            status=MAPPING_ACTIVE,
        )
        db.session.add(self.mapping)
        db.session.commit()
        SlotGenerationService.generate_partner_daily_slots(self.partner.id, days=2)

        self.admin_token = create_access_token(
            identity=self.admin.id,
            additional_claims={"role": "ADMIN", "email": self.admin.email},
        )
        self.other_token = create_access_token(
            identity=self.other.id,
            additional_claims={"role": "PATIENT", "email": self.other.email},
        )
        self.spoofed_admin_token = create_access_token(
            identity=self.other.id,
            additional_claims={"role": "SUPER_ADMIN", "email": self.admin.email},
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _auth(self, token=None, **extra):
        headers = {"Authorization": f"Bearer {token or self.admin_token}"}
        headers.update(extra)
        return headers

    def _booking_payload(self, name="P06 Patient"):
        return {
            "partner_service_mapping_id": self.mapping.id,
            "patient_name": name,
            "patient_phone": "0901234567",
            "requested_date": "2026-08-12",
            "requested_time_slot": "08:00-10:00",
        }

    def test_anonymous_marketplace_booking_denied(self):
        resp = self.client.post("/api/v1/marketplace/bookings", json=self._booking_payload())
        self.assertEqual(resp.status_code, 401)

    def test_anonymous_payment_create_denied(self):
        resp = self.client.post(
            "/api/v1/payments/create",
            json={"invoice_id": "missing", "provider": PAYMENT_PROVIDER_STRIPE},
        )
        self.assertEqual(resp.status_code, 401)

    def test_anonymous_federation_write_denied(self):
        resp = self.client.post("/api/v1/federation/labs", json={"name": "Anon Lab"})
        self.assertEqual(resp.status_code, 401)

    def test_anonymous_integration_connection_denied(self):
        resp = self.client.post(
            "/api/v1/integrations/connections",
            json={"partner_code": "LIS-ANON", "partner_name": "Anon"},
        )
        self.assertEqual(resp.status_code, 401)

    def test_anonymous_partner_write_denied(self):
        resp = self.client.post(
            "/api/v1/partners",
            json={"partner_type": "LABORATORY", "legal_name": "Anon Lab"},
        )
        self.assertEqual(resp.status_code, 401)

    def test_spoofed_email_without_jwt_still_401(self):
        resp = self.client.post(
            "/api/v1/marketplace/bookings",
            headers={"X-User-Email": self.admin.email, "X-User-Role": "SUPER_ADMIN"},
            json=self._booking_payload(),
        )
        self.assertEqual(resp.status_code, 401)

    def test_authenticated_marketplace_booking_succeeds(self):
        resp = self.client.post(
            "/api/v1/marketplace/bookings",
            headers=self._auth(),
            json=self._booking_payload("Auth Patient"),
        )
        self.assertEqual(resp.status_code, 201, resp.get_json())
        booking = resp.get_json()["booking"]
        row = AuditLog.query.filter_by(
            action="MARKETPLACE_BOOKING_CREATED",
            object_id=booking["id"],
        ).first()
        self.assertIsNotNone(row)
        self.assertEqual(row.user_email, self.admin.email)

    def test_spoofed_x_user_email_cannot_impersonate_audit_actor(self):
        resp = self.client.post(
            "/api/v1/marketplace/bookings",
            headers=self._auth(**{"X-User-Email": self.other.email}),
            json=self._booking_payload("Spoof Patient"),
        )
        self.assertEqual(resp.status_code, 201, resp.get_json())
        booking = resp.get_json()["booking"]
        row = AuditLog.query.filter_by(
            action="MARKETPLACE_BOOKING_CREATED",
            object_id=booking["id"],
        ).first()
        self.assertEqual(row.user_email, self.admin.email)
        self.assertNotEqual(row.user_email, self.other.email)

    def test_spoofed_x_user_role_cannot_elevate(self):
        resp = self.client.post(
            "/api/v1/security/users",
            headers=self._auth(
                self.other_token,
                **{"X-User-Role": "SUPER_ADMIN", "X-User-Email": self.admin.email},
            ),
            json={
                "email": f"p06-elev-{uuid.uuid4().hex[:8]}@test.local",
                "password": PASSWORD,
                "role": "ADMIN",
            },
        )
        self.assertIn(resp.status_code, (401, 403))

    def test_stale_role_claim_cannot_elevate(self):
        resp = self.client.post(
            "/api/v1/security/users",
            headers=self._auth(self.spoofed_admin_token),
            json={
                "email": f"p06-claim-{uuid.uuid4().hex[:8]}@test.local",
                "password": PASSWORD,
                "role": "ADMIN",
            },
        )
        self.assertIn(resp.status_code, (401, 403))

    def test_public_marketplace_search_remains_open(self):
        resp = self.client.get("/api/v1/marketplace/search?q=Glucose")
        self.assertEqual(resp.status_code, 200)

    def test_public_catalog_search_remains_open(self):
        resp = self.client.get("/api/v1/marketplace/catalog/search")
        self.assertEqual(resp.status_code, 200)

    def test_public_marketplace_health_remains_open(self):
        resp = self.client.get("/api/v1/marketplace/v2/health")
        self.assertEqual(resp.status_code, 200)

    def test_payment_webhook_remains_public(self):
        resp = self.client.post(
            "/api/v1/payments/webhook",
            json={
                "provider": PAYMENT_PROVIDER_STRIPE,
                "event_type": "payment.updated",
                "external_transaction_id": "missing-txn",
                "status": PAYMENT_GATEWAY_COMPLETED,
            },
        )
        self.assertNotEqual(resp.status_code, 401)
        self.assertNotEqual(resp.status_code, 403)

    def test_lis_ingest_remains_without_jwt_service_auth_gap(self):
        create = self.client.post(
            "/api/v1/integrations/connections",
            headers=self._auth(),
            json={
                "partner_code": "LIS-P06",
                "partner_name": "P06 LIS",
                "integration_type": "LIS",
                "connection_code": "LIS-P06-CONN",
            },
        )
        self.assertEqual(create.status_code, 201, create.get_json())
        conn_id = create.get_json()["connection"]["id"]
        resp = self.client.post(
            "/api/v1/integrations/lis/orders",
            json={
                "connection_id": conn_id,
                "external_order_id": "LIS-P06-1",
                "patient_code": "PAT-P06",
                "test_codes": ["GLU"],
            },
        )
        self.assertEqual(resp.status_code, 201, resp.get_json())

    def test_tenant_header_cannot_select_foreign_org_for_marketplace_listing(self):
        resp = self.client.post(
            "/api/v1/marketplace/v2/listings",
            headers=self._auth(
                self.other_token,
                **{"X-Organization-Id": self.org_a.id},
            ),
            json={"title": "Foreign listing", "base_price": 1},
        )
        self.assertEqual(resp.status_code, 403)

    def test_iot_device_register_requires_human_auth(self):
        resp = self.client.post(
            "/api/v1/iot/devices",
            json={"device_code": "IOT-P06-ANON", "device_type": "COLD_BOX"},
        )
        self.assertEqual(resp.status_code, 401)

    def test_authenticated_iot_device_register_succeeds(self):
        resp = self.client.post(
            "/api/v1/iot/devices",
            headers=self._auth(),
            json={"device_code": "IOT-P06-OK", "device_type": "COLD_BOX"},
        )
        self.assertEqual(resp.status_code, 201, resp.get_json())

    def test_anonymous_patient_create_denied(self):
        resp = self.client.post(
            "/api/v1/patients",
            json={"patient_code": "P06-ANON", "full_name": "Anon"},
        )
        self.assertEqual(resp.status_code, 401)

    def test_anonymous_order_create_denied(self):
        resp = self.client.post(
            "/api/v1/orders",
            json={"order_code": "P06-ANON", "total_amount": 1},
        )
        self.assertEqual(resp.status_code, 401)

    def test_anonymous_ai_clinical_interpret_denied(self):
        resp = self.client.post(
            "/api/v1/ai-clinical/interpret",
            json={"items": [{"test_code": "GLU", "result_value": "1"}]},
        )
        self.assertEqual(resp.status_code, 401)

    def test_anonymous_api_key_create_denied(self):
        resp = self.client.post("/api/v1/api-keys", json={"client_id": "missing"})
        self.assertEqual(resp.status_code, 401)

    def test_authenticated_patient_create_succeeds(self):
        resp = self.client.post(
            "/api/v1/patients",
            headers=self._auth(),
            json={
                "patient_code": f"P06-{uuid.uuid4().hex[:8].upper()}",
                "full_name": "P06 Patient",
            },
        )
        self.assertEqual(resp.status_code, 201, resp.get_json())


class P06ProductionGateTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(
            {
                "TESTING": False,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "API_AUTH_GATE_ENABLED": True,
                "APP_ENV": "production",
                "DEMO_MODE": False,
                "RATE_LIMIT_ENABLED": False,
                "SECRET_KEY": "p06-test-secret-key-not-for-prod",
                "JWT_SECRET_KEY": "p06-test-jwt-secret-key-not-for-prod",
            }
        )
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_patients_require_auth_in_production(self):
        resp = self.client.post("/api/v1/patients", json={})
        self.assertEqual(resp.status_code, 401)

    def test_ai_clinical_require_auth_in_production(self):
        resp = self.client.post("/api/v1/ai-clinical/interpret", json={})
        self.assertEqual(resp.status_code, 401)

    def test_marketplace_bookings_require_auth_in_production(self):
        resp = self.client.post("/api/v1/marketplace/bookings", json={})
        self.assertEqual(resp.status_code, 401)

    def test_payments_create_require_auth_in_production(self):
        resp = self.client.post("/api/v1/payments/create", json={})
        self.assertEqual(resp.status_code, 401)

    def test_payment_webhook_public_in_production(self):
        resp = self.client.post(
            "/api/v1/payments/webhook",
            json={"provider": "STRIPE", "event_type": "payment.updated"},
        )
        self.assertNotEqual(resp.status_code, 401)

    def test_marketplace_search_public_in_production(self):
        resp = self.client.get("/api/v1/marketplace/search")
        self.assertNotEqual(resp.status_code, 401)

    def test_health_remains_public(self):
        resp = self.client.get("/api/v1/system/health")
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
