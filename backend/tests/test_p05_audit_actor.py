"""P0-5: audit actor must be server-derived (human identity or authenticated device)."""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_p05_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from flask_jwt_extended import create_access_token

from app import create_app
from app.core.audit import write_audit
from app.core.audit_actor import (
    canonicalize_audit_actor,
    contains_secret_material,
    resolve_human_audit_actor,
    sanitize_audit_payload,
    system_audit_actor,
)
from app.core.passwords import hash_password
from app.extensions.db import db
from app.models.audit_log import AuditLog
from app.models.user import User


PASSWORD = "Password123!"


class AuditActorP05Tests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["API_AUTH_GATE_ENABLED"] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()

        self.admin = User(
            email=f"p05-admin-{uuid.uuid4().hex[:8]}@test.local",
            role="ADMIN",
            password_hash=hash_password(PASSWORD),
            is_active=True,
        )
        self.other = User(
            email=f"p05-other-{uuid.uuid4().hex[:8]}@test.local",
            role="DOCTOR",
            password_hash=hash_password(PASSWORD),
            is_active=True,
        )
        db.session.add_all([self.admin, self.other])
        db.session.commit()
        self.admin_token = create_access_token(
            identity=self.admin.id,
            additional_claims={"role": "ADMIN", "email": self.admin.email},
        )
        self.other_token = create_access_token(
            identity=self.other.id,
            additional_claims={"role": "DOCTOR", "email": self.other.email},
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _auth(self, token=None, **extra):
        headers = {"Authorization": f"Bearer {token or self.admin_token}"}
        headers.update(extra)
        return headers

    def _latest_create_user_audit(self):
        return (
            AuditLog.query.filter_by(action="CREATE_USER")
            .order_by(AuditLog.created_at.desc())
            .first()
        )

    def test_authenticated_human_no_header_is_audit_actor(self):
        email = f"p05-a-{uuid.uuid4().hex[:8]}@test.local"
        resp = self.client.post(
            "/api/v1/security/users",
            headers=self._auth(),
            json={"email": email, "password": PASSWORD, "role": "PATIENT"},
        )
        self.assertEqual(resp.status_code, 201, resp.get_json())
        row = self._latest_create_user_audit()
        self.assertIsNotNone(row)
        self.assertEqual(row.user_email, self.admin.email)
        self.assertNotIn("password", (row.user_email or "").lower())

    def test_spoofed_x_user_email_does_not_become_audit_actor(self):
        email = f"p05-b-{uuid.uuid4().hex[:8]}@test.local"
        resp = self.client.post(
            "/api/v1/security/users",
            headers=self._auth(**{"X-User-Email": "attacker@evil.local"}),
            json={"email": email, "password": PASSWORD, "role": "PATIENT"},
        )
        self.assertEqual(resp.status_code, 201, resp.get_json())
        row = self._latest_create_user_audit()
        self.assertIsNotNone(row)
        self.assertEqual(row.user_email, self.admin.email)
        self.assertNotEqual(row.user_email, "attacker@evil.local")

    def test_different_spoofed_email_never_audited(self):
        email = f"p05-c-{uuid.uuid4().hex[:8]}@test.local"
        resp = self.client.post(
            "/api/v1/security/users",
            headers=self._auth(
                **{
                    "X-User-Email": self.other.email,
                    "X-User-Role": "SUPER_ADMIN",
                    "X-Actor": "system",
                }
            ),
            json={"email": email, "password": PASSWORD, "role": "PATIENT"},
        )
        self.assertEqual(resp.status_code, 201, resp.get_json())
        row = self._latest_create_user_audit()
        self.assertEqual(row.user_email, self.admin.email)
        self.assertNotEqual(row.user_email, self.other.email)
        self.assertNotEqual(row.user_email, "system")
        self.assertNotEqual(row.user_email, "SYSTEM")

    def test_client_cannot_choose_audit_actor_via_enterprise_api(self):
        resp = self.client.post(
            "/api/v1/audit/records",
            headers=self._auth(),
            json={
                "action": "P05_SPOOF_ACTOR",
                "actor_email": "chosen@evil.local",
                "payload": {"password": PASSWORD, "note": "ok"},
            },
        )
        self.assertEqual(resp.status_code, 201, resp.get_json())
        body = resp.get_json() or {}
        actor = (
            body.get("actor_email")
            or body.get("record", {}).get("actor_email")
            or body.get("user_email")
        )
        if actor:
            self.assertEqual(actor, self.admin.email)
            self.assertNotEqual(actor, "chosen@evil.local")

    def test_system_actor_is_server_controlled(self):
        self.assertEqual(system_audit_actor("payment_webhook"), "system:payment_webhook")
        self.assertEqual(system_audit_actor("X-User-Email: system"), "system:job")
        with self.app.test_request_context("/api/v1/payments/webhook"):
            self.assertEqual(canonicalize_audit_actor("attacker@evil.local"), "SYSTEM")
            self.assertEqual(canonicalize_audit_actor("system:payment_webhook"), "system:payment_webhook")

    def test_write_audit_ignores_spoof_when_identity_bound(self):
        with self.app.test_request_context(
            "/api/v1/security/users",
            headers=self._auth(**{"X-User-Email": "spoof@evil.local"}),
        ):
            from app.core.authenticated_identity import bind_authenticated_identity

            bind_authenticated_identity()
            write_audit("P05_TEST", "TEST", "1", user_email="spoof@evil.local")
            db.session.commit()
        row = (
            AuditLog.query.filter_by(action="P05_TEST")
            .order_by(AuditLog.created_at.desc())
            .first()
        )
        self.assertIsNotNone(row)
        self.assertEqual(row.user_email, self.admin.email)

    def test_unauthenticated_request_cannot_set_header_actor(self):
        with self.app.test_request_context(
            "/api/v1/marketplace/bookings",
            headers={"X-User-Email": "spoof@evil.local"},
        ):
            self.assertEqual(resolve_human_audit_actor(), "SYSTEM")
            write_audit("P05_ANON", "TEST", "2", user_email="spoof@evil.local")
            db.session.commit()
        row = AuditLog.query.filter_by(action="P05_ANON").first()
        self.assertEqual(row.user_email, "SYSTEM")
        self.assertNotEqual(row.user_email, "spoof@evil.local")

    def test_secrets_never_stored_as_audit_actor(self):
        self.assertTrue(contains_secret_material("Bearer abc.def"))
        self.assertTrue(contains_secret_material("password_hash:pbkdf2"))
        redacted = sanitize_audit_payload(
            {
                "password": PASSWORD,
                "password_hash": "pbkdf2:sha256:x",
                "device_secret": "DXCON-IOT-INGEST-SECRET",
                "ok": "visible",
            }
        )
        self.assertEqual(redacted["password"], "[REDACTED]")
        self.assertEqual(redacted["password_hash"], "[REDACTED]")
        self.assertEqual(redacted["device_secret"], "[REDACTED]")
        self.assertEqual(redacted["ok"], "visible")

    def test_spoofed_org_header_does_not_become_actor(self):
        email = f"p05-d-{uuid.uuid4().hex[:8]}@test.local"
        resp = self.client.post(
            "/api/v1/security/users",
            headers=self._auth(
                **{
                    "X-Organization-ID": "org-spoof",
                    "X-Partner-ID": "partner-spoof",
                    "X-User-Email": "spoof@evil.local",
                }
            ),
            json={"email": email, "password": PASSWORD, "role": "PATIENT"},
        )
        self.assertEqual(resp.status_code, 201, resp.get_json())
        row = self._latest_create_user_audit()
        self.assertEqual(row.user_email, self.admin.email)
        self.assertNotIn("org-spoof", row.user_email)
        self.assertNotIn("partner-spoof", row.user_email)


class DeviceAuditActorP05Tests(unittest.TestCase):
    def setUp(self):
        from app.services.iot_cold_chain_service import IoTDeviceService

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.device_secret = "DXCON-IOT-INGEST-SECRET"
        self.device_a = IoTDeviceService.register_device(
            {
                "device_code": "P05-IOT-A",
                "box_code": "P05-BOX-A",
                "device_type": "COLD_BOX",
                "serial_number": "P05-SN-A",
                "partner_id": "ORG-A",
                "ingest_secret": self.device_secret,
            }
        )["device"]
        self.device_b = IoTDeviceService.register_device(
            {
                "device_code": "P05-IOT-B",
                "box_code": "P05-BOX-B",
                "device_type": "COLD_BOX",
                "serial_number": "P05-SN-B",
                "partner_id": "ORG-B",
                "ingest_secret": self.device_secret,
            }
        )["device"]
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _headers(self, device, **extra):
        headers = {"X-Device-Id": device["id"], "X-Device-Secret": self.device_secret}
        headers.update(extra)
        return headers

    def _ingest(self, device, payload, *, headers=None):
        p = dict(payload)
        p.setdefault("device_id", device["id"])
        p.setdefault("event_id", f"evt-{uuid.uuid4().hex[:8]}")
        return self.client.post(
            "/api/v1/iot-logistics/ingest",
            headers=headers or self._headers(device),
            json={"adapter_type": "GENERIC", "payload": p},
        )

    def test_authenticated_device_audit_actor_is_device(self):
        from app.models.logistics_tracking import ChainOfCustodyEvent

        resp = self._ingest(self.device_a, {"event_type": "TEMPERATURE", "celsius": 4.5})
        self.assertEqual(resp.status_code, 200, resp.get_json())
        event = (
            ChainOfCustodyEvent.query.filter_by(
                reference_type="IoTDevice", reference_id=self.device_a["id"]
            )
            .order_by(ChainOfCustodyEvent.created_at.desc())
            .first()
        )
        self.assertIsNotNone(event)
        self.assertEqual(event.actor, f"device:{self.device_a['device_code']}")

    def test_spoofed_payload_device_id_rejected(self):
        resp = self._ingest(
            self.device_a,
            {"event_type": "TEMPERATURE", "celsius": 4.5, "device_id": self.device_b["id"]},
        )
        self.assertIn(resp.status_code, {400, 403})

    def test_spoofed_x_device_id_rejected(self):
        resp = self._ingest(
            self.device_a,
            {"event_type": "TEMPERATURE", "celsius": 4.5},
            headers={
                "X-Device-Id": self.device_b["id"],
                "X-Device-Secret": self.device_secret,
            },
        )
        # Secret may match both demo devices; payload bind still rejects org/id mismatch
        # when device B header is used with device A payload id.
        self.assertIn(resp.status_code, {400, 403})

    def test_device_a_cannot_claim_organization_b(self):
        resp = self._ingest(
            self.device_a,
            {
                "event_type": "TEMPERATURE",
                "celsius": 4.5,
                "organization_id": "ORG-B",
                "partner_id": "ORG-B",
            },
        )
        self.assertIn(resp.status_code, {400, 403})

    def test_human_session_cannot_use_device_actor(self):
        user = User(
            email="p05-human-device@test.local",
            role="ADMIN",
            password_hash=hash_password(PASSWORD),
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        with self.client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["email"] = user.email
        resp = self.client.post(
            "/api/v1/iot-logistics/ingest",
            json={
                "adapter_type": "GENERIC",
                "payload": {
                    "event_type": "TEMPERATURE",
                    "device_id": self.device_a["id"],
                    "celsius": 4.5,
                    "event_id": "human-evt",
                },
            },
        )
        self.assertEqual(resp.status_code, 401)

    def test_device_request_does_not_audit_as_human(self):
        from app.models.logistics_tracking import ChainOfCustodyEvent

        resp = self._ingest(
            self.device_a,
            {"event_type": "TEMPERATURE", "celsius": 4.5},
            headers=self._headers(self.device_a, **{"X-User-Email": "human@evil.local"}),
        )
        self.assertEqual(resp.status_code, 200, resp.get_json())
        event = (
            ChainOfCustodyEvent.query.filter_by(
                reference_type="IoTDevice", reference_id=self.device_a["id"]
            )
            .order_by(ChainOfCustodyEvent.created_at.desc())
            .first()
        )
        self.assertEqual(event.actor, f"device:{self.device_a['device_code']}")
        self.assertNotEqual(event.actor, "human@evil.local")


if __name__ == "__main__":
    unittest.main()
