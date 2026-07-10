"""Tests for Mobile MVP API — Epic 7."""

from __future__ import annotations

import os
import unittest
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.extensions.db import db
from app.mobile_mvp.models import MobileDevice
from app.models.driver import Driver
from app.models.user import User
from app.patient_marketplace.models import MpBooking, MpListing, MpProvider, MpService
from flask_jwt_extended import create_access_token


class MobileMvpTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.user = User(
            id=str(uuid.uuid4()),
            email="patient-mobile@example.com",
            role="PATIENT",
            password_hash="x",
            phone="0900000001",
        )
        db.session.add(self.user)
        self.collector_user = User(
            id=str(uuid.uuid4()),
            email="collector@example.com",
            role="COLLECTOR",
            password_hash="x",
        )
        db.session.add(self.collector_user)
        self.collector = Driver(
            id=str(uuid.uuid4()),
            driver_code="COL-001",
            full_name="Nguyen Van A",
        )
        db.session.add(self.collector)
        self.org_id = str(uuid.uuid4())
        provider = MpProvider(
            id=str(uuid.uuid4()),
            organization_id=self.org_id,
            provider_code="LAB-01",
            provider_name="Test Lab",
            provider_type="LABORATORY",
        )
        service = MpService(
            id=str(uuid.uuid4()),
            organization_id=self.org_id,
            service_code="CBC",
            service_name="Complete Blood Count",
            service_type="LAB_TEST",
        )
        listing = MpListing(
            id=str(uuid.uuid4()),
            organization_id=self.org_id,
            provider_id=provider.id,
            service_id=service.id,
            listing_code="LST-001",
            title="CBC Test",
            base_price=100000,
            status="ACTIVE",
        )
        self.booking = MpBooking(
            id=str(uuid.uuid4()),
            booking_code="BK-TEST001",
            patient_user_id=self.user.id,
            organization_id=self.org_id,
            provider_id=provider.id,
            listing_id=listing.id,
            booking_status="CONFIRMED",
        )
        db.session.add_all([provider, service, listing, self.booking])
        db.session.commit()
        self.patient_token = create_access_token(
            identity=self.user.id, additional_claims={"role": self.user.role}
        )
        self.collector_token = create_access_token(
            identity=self.collector_user.id, additional_claims={"role": self.collector_user.role}
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _auth(self, token: str, org: str | None = None):
        headers = {"Authorization": f"Bearer {token}"}
        if org:
            headers["X-Organization-Id"] = org
        return headers

    def test_app_config_public(self):
        res = self.client.get("/api/v1/mobile/app-config")
        self.assertEqual(res.status_code, 200)
        self.assertIn("min_supported_version", res.get_json()["data"])

    def test_register_device(self):
        res = self.client.post(
            "/api/v1/mobile/devices",
            json={"platform": "android", "app_version": "2.0.0", "device_reference": "dev-test-1"},
            headers=self._auth(self.patient_token, self.org_id),
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(MobileDevice.query.count(), 1)

    def test_patient_dashboard(self):
        res = self.client.get(
            "/api/v1/mobile/patient/dashboard",
            headers=self._auth(self.patient_token, self.org_id),
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("recent_bookings", res.get_json()["data"])

    def test_patient_booking_detail_denied_for_other_user(self):
        other = User(id=str(uuid.uuid4()), email="other@example.com", role="PATIENT", password_hash="x")
        db.session.add(other)
        db.session.commit()
        token = create_access_token(identity=other.id, additional_claims={"role": "PATIENT"})
        res = self.client.get(
            f"/api/v1/mobile/patient/bookings/{self.booking.id}",
            headers=self._auth(token, self.org_id),
        )
        self.assertEqual(res.status_code, 404)

    def test_collector_jobs_scope(self):
        res = self.client.get(
            f"/api/v1/mobile/collector/jobs?collector_id={self.collector.id}",
            headers=self._auth(self.collector_token),
        )
        self.assertEqual(res.status_code, 200)

    def test_collector_unauthorized_other_collector(self):
        other_collector = Driver(id=str(uuid.uuid4()), driver_code="COL-999", full_name="Other", email="x@y.com")
        db.session.add(other_collector)
        db.session.commit()
        res = self.client.get(
            f"/api/v1/mobile/collector/jobs?collector_id={other_collector.id}",
            headers=self._auth(self.patient_token),
        )
        self.assertEqual(res.status_code, 403)


if __name__ == "__main__":
    unittest.main()
