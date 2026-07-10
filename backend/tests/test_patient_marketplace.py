"""Tests for Patient Marketplace — Epic 5."""

from __future__ import annotations

import hashlib
import hmac
import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.extensions.db import db
from app.patient_marketplace.models import MpListing, MpProvider, MpService
from app.patient_marketplace.service import BookingService, PaymentService, PricingService, SearchService
from app.partner_foundation.service import ensure_default_organization


class PatientMarketplaceTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.org = ensure_default_organization()
        self.provider = MpProvider(
            organization_id=self.org.id,
            provider_code="PRV-TEST",
            provider_name="Test Lab",
            provider_type="LABORATORY",
            verified=True,
            address="Ho Chi Minh City",
            latitude=10.7769,
            longitude=106.7009,
            public_status="ACTIVE",
        )
        self.service = MpService(
            organization_id=self.org.id,
            service_code="CBC",
            service_name="Complete Blood Count",
            service_type="LAB_TEST",
        )
        db.session.add_all([self.provider, self.service])
        db.session.commit()
        self.listing = MpListing(
            organization_id=self.org.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            listing_code="LST-TEST",
            title="CBC Test Package",
            status="ACTIVE",
            base_price=250000,
            partner_consent=True,
            home_collection_available=True,
            service_radius_km=20,
        )
        db.session.add(self.listing)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_search_active_listings_only(self):
        draft = MpListing(
            organization_id=self.org.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            listing_code="LST-DRAFT",
            title="Draft",
            status="DRAFT",
            base_price=100000,
        )
        db.session.add(draft)
        db.session.commit()
        result = SearchService.search_listings()
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["listings"][0]["listing_code"], "LST-TEST")

    def test_pricing_snapshot(self):
        quote = PricingService.quote(self.listing.id, distance_km=5)
        self.assertIn("pricing_snapshot_id", quote)
        self.assertGreater(quote["total_amount"], 250000)

    def test_booking_idempotency(self):
        data = {"listing_id": self.listing.id, "idempotency_key": "idem-1", "contact_phone": "090"}
        b1 = BookingService.create_booking(data, self.org.id)
        db.session.commit()
        b2 = BookingService.create_booking(data, self.org.id)
        self.assertEqual(b1["booking_code"], b2["booking_code"])

    def test_qr_payment_webhook(self):
        booking = BookingService.create_booking({"listing_id": self.listing.id}, self.org.id)
        db.session.commit()
        payment = PaymentService.create_qr_payment(booking["id"], self.org.id)
        db.session.commit()
        secret = "test-secret"
        amount = payment["amount"]
        ref = payment["payment_reference"]
        sig = hmac.new(secret.encode(), f"{ref}:{amount}".encode(), hashlib.sha256).hexdigest()
        os.environ["MARKETPLACE_PAYMENT_WEBHOOK_SECRET"] = secret
        result = PaymentService.handle_webhook(
            {"payment_reference": ref, "amount": amount, "idempotency_key": "wh-1"},
            sig,
            secret,
        )
        self.assertEqual(result["status"], "SUCCEEDED")

    def test_catalog_routes(self):
        res = self.client.get("/api/v1/marketplace/catalog/search")
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(res.get_json()["count"], 1)

    def test_health(self):
        res = self.client.get("/api/v1/marketplace/v2/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["module"], "patient_marketplace")


if __name__ == "__main__":
    unittest.main()
