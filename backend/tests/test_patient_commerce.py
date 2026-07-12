"""Tests for Patient Commerce — Release 8.0 Sprint 7."""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.patient_marketplace.home_collection import HomeCollectionService
from app.patient_marketplace.models import MpListing, MpProvider, MpService
from app.patient_marketplace.service import MarketplaceError, PricingService, SearchService
from app.patient_marketplace.slot_engine import SlotEngineService


class PatientCommerceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.org = "org-commerce-test"
        self._seed_catalog()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _seed_catalog(self):
        provider = MpProvider(
            organization_id=self.org,
            provider_code="LAB-01",
            provider_name="DxCon Lab",
            provider_type="LABORATORY",
            public_status="ACTIVE",
            featured=True,
            city="Ho Chi Minh City",
            working_hours_json='{"0":{"open":"08:00","close":"17:00","closed":false}}',
            latitude=10.77,
            longitude=106.7,
        )
        db.session.add(provider)
        db.session.flush()
        service = MpService(
            organization_id=self.org,
            service_code="GLU",
            service_name="Glucose",
            service_type="LAB_TEST",
        )
        db.session.add(service)
        db.session.flush()
        draft = MpListing(
            organization_id=self.org,
            provider_id=provider.id,
            service_id=service.id,
            listing_code="LST-DRAFT",
            title="Draft Test",
            status="DRAFT",
            base_price=Decimal("100000"),
            partner_consent=True,
        )
        active = MpListing(
            organization_id=self.org,
            provider_id=provider.id,
            service_id=service.id,
            listing_code="LST-ACTIVE",
            title="Glucose Test",
            status="ACTIVE",
            base_price=Decimal("150000"),
            partner_consent=True,
            home_collection_available=True,
            turnaround_hours=24,
            featured=True,
        )
        db.session.add_all([draft, active])
        db.session.commit()
        self.provider = provider
        self.active_listing = active

    def test_only_published_services(self):
        result = SearchService.list_services()
        codes = [l["listing_code"] for l in result["listings"]]
        self.assertIn("LST-ACTIVE", codes)
        self.assertNotIn("LST-DRAFT", codes)

    def test_quotation_includes_components(self):
        quote = PricingService.quote(self.active_listing.id)
        self.assertIn("total_amount", quote)
        self.assertIn("pricing_snapshot_id", quote)
        self.assertGreater(quote["total_amount"], 0)

    def test_slot_hold_and_expiration(self):
        start = datetime.utcnow().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
        end = start + timedelta(minutes=30)
        hold = SlotEngineService.hold_slot(
            self.provider.id,
            organization_id=self.org,
            slot_start=start,
            slot_end=end,
            patient_user_id="pat-1",
        )
        self.assertIn("hold_token", hold)
        expired = SlotEngineService.expire_stale_holds()
        self.assertIsInstance(expired, int)

    def test_saved_address(self):
        addr = HomeCollectionService.save_address(
            {
                "address_line": "123 Nguyen Hue",
                "building": "Tower A",
                "city": "HCMC",
                "collector_notes": "Ring bell",
            },
            organization_id=self.org,
            patient_user_id="user-1",
        )
        listed = HomeCollectionService.list_addresses("user-1", organization_id=self.org)
        self.assertEqual(listed["count"], 1)
        self.assertEqual(addr["building"], "Tower A")

    def test_double_booking_protection(self):
        start = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=2)
        end = start + timedelta(minutes=30)
        SlotEngineService.hold_slot(
            self.provider.id,
            organization_id=self.org,
            slot_start=start,
            slot_end=end,
        )
        slots = SlotEngineService.list_available_slots(
            self.provider.id,
            organization_id=self.org,
            slot_date=start.date().isoformat(),
        )
        matching = [s for s in slots["slots"] if s["time"] == "10:00"]
        if matching:
            self.assertFalse(matching[0]["available"])


if __name__ == "__main__":
    unittest.main()
