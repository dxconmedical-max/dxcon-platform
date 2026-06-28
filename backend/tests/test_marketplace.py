import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
    BOOKING_TIMELINE_CONFIRMED,
    BOOKING_TIMELINE_CREATED,
    MAPPING_ACTIVE,
    PARTNER_ACTIVE,
    RECOMMENDATION_TAG_FAST_RESULT,
    RECOMMENDATION_TAG_TOP_RATED,
)
from app.extensions.db import db
from app.models.audit_log import AuditLog
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.models.event_log import EventLog
from app.models.marketplace_booking_timeline import MarketplaceBookingTimeline
from app.models.partner import Partner
from app.models.partner_availability import PartnerAvailability
from app.models.partner_service_mapping import PartnerServiceMapping
from app.services.partner_availability import PartnerAvailabilityService
from app.services.ranking_service import RankingService


class MarketplaceFoundationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.category = DiagnosticCategory(
            category_code="BIOCHEM",
            name="Biochemistry",
            is_active=True,
        )
        db.session.add(self.category)
        db.session.flush()

        self.service = DiagnosticService(
            service_code="HBA1C",
            name="HbA1c",
            short_name="HbA1c",
            category_id=self.category.id,
            sample_type="Whole Blood",
            estimated_turnaround_hours=24,
            home_collection_allowed=True,
            is_active=True,
        )
        db.session.add(self.service)

        self.partner = Partner(
            partner_code="PTR-DEM-0001",
            partner_type="LABORATORY",
            legal_name="Demo Lab",
            display_name="Demo Lab Hanoi",
            province="Ha Noi",
            city="Ha Noi",
            district="Cau Giay",
            status=PARTNER_ACTIVE,
            rating=4.6,
            review_count=120,
            completed_orders=500,
            average_result_time_hours=12,
        )
        db.session.add(self.partner)
        db.session.flush()

        self.mapping = PartnerServiceMapping(
            partner_id=self.partner.id,
            diagnostic_service_id=self.service.id,
            partner_service_code="DEMO-HBA1C",
            partner_service_name="HbA1c",
            price=180000,
            currency="VND",
            turnaround_hours=24,
            home_collection_available=True,
            status=MAPPING_ACTIVE,
        )
        db.session.add(self.mapping)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_search_returns_ranked_results_with_tags(self):
        response = self.client.get("/api/v1/marketplace/search?q=HbA1c&city=Ha%20Noi")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["count"], 1)
        result = body["results"][0]
        self.assertEqual(result["service"]["service_code"], "HBA1C")
        self.assertIn("trust_score", result)
        self.assertIn("recommendation_tags", result)
        self.assertIsInstance(result["recommendation_tags"], list)
        self.assertIn(RECOMMENDATION_TAG_TOP_RATED, result["recommendation_tags"])
        self.assertIn("recommendation_reason", result)
        self.assertIn("availability", result)
        self.assertIn("book_url", result)

    def test_ranking_penalizes_nearly_full_partner(self):
        availability = PartnerAvailability(
            partner_id=self.partner.id,
            date="2026-06-26",
            maximum_daily_capacity=10,
            booked_count=9,
            available_slots=1,
        )
        open_ranking = RankingService.score_mapping(
            self.partner,
            self.mapping,
            self.service,
            [],
            PartnerAvailability(
                partner_id=self.partner.id,
                date="2026-06-26",
                maximum_daily_capacity=10,
                booked_count=2,
                available_slots=8,
            ),
        )
        full_ranking = RankingService.score_mapping(
            self.partner,
            self.mapping,
            self.service,
            [],
            availability,
        )
        self.assertGreater(open_ranking["trust_score"], full_ranking["trust_score"])
        self.assertGreater(full_ranking["capacity_penalty"], 0)

    def test_create_booking_writes_timeline_audit_and_event(self):
        response = self.client.post(
            "/api/v1/marketplace/bookings",
            json={
                "partner_service_mapping_id": self.mapping.id,
                "patient_name": "Nguyen Van A",
                "patient_phone": "0901234567",
                "requested_date": "2026-06-26",
                "requested_time_slot": "08:00-10:00",
            },
        )
        self.assertEqual(response.status_code, 201)
        booking = response.get_json()["booking"]
        self.assertTrue(booking["booking_code"].startswith("DXM-"))

        timeline = MarketplaceBookingTimeline.query.filter_by(
            booking_id=booking["id"],
            event_type=BOOKING_TIMELINE_CREATED,
        ).first()
        self.assertIsNotNone(timeline)

        audit = AuditLog.query.filter_by(
            action="MARKETPLACE_BOOKING_CREATED",
            object_id=booking["id"],
        ).first()
        self.assertIsNotNone(audit)

        event = EventLog.query.filter_by(
            event_type="MARKETPLACE_BOOKING_CREATED",
            object_id=booking["id"],
        ).first()
        self.assertIsNotNone(event)

        availability = PartnerAvailability.query.filter_by(
            partner_id=self.partner.id,
            date="2026-06-26",
        ).first()
        self.assertIsNotNone(availability)
        self.assertEqual(availability.booked_count, 1)

    def test_booking_transition_writes_timeline(self):
        create_response = self.client.post(
            "/api/v1/marketplace/bookings",
            json={
                "partner_service_mapping_id": self.mapping.id,
                "patient_name": "Tran Thi B",
                "patient_phone": "0907654321",
                "requested_date": "2026-06-27",
            },
        )
        booking_id = create_response.get_json()["booking"]["id"]

        transition_response = self.client.post(
            f"/api/v1/marketplace/bookings/{booking_id}/transition",
            json={"event_type": BOOKING_TIMELINE_CONFIRMED},
        )
        self.assertEqual(transition_response.status_code, 200)

        events = MarketplaceBookingTimeline.query.filter_by(booking_id=booking_id).all()
        event_types = [event.event_type for event in events]
        self.assertIn(BOOKING_TIMELINE_CREATED, event_types)
        self.assertIn(BOOKING_TIMELINE_CONFIRMED, event_types)

    def test_list_and_get_booking_detail_with_timeline(self):
        create_response = self.client.post(
            "/api/v1/marketplace/bookings",
            json={
                "partner_service_mapping_id": self.mapping.id,
                "patient_name": "Tran Thi B",
                "patient_phone": "0907654321",
                "requested_date": "2026-06-28",
            },
        )
        booking_id = create_response.get_json()["booking"]["id"]

        list_response = self.client.get("/api/v1/marketplace/bookings")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.get_json()["count"], 1)

        detail_response = self.client.get(f"/api/v1/marketplace/bookings/{booking_id}")
        self.assertEqual(detail_response.status_code, 200)
        body = detail_response.get_json()
        self.assertEqual(body["patient_name"], "Tran Thi B")
        self.assertTrue(len(body["timeline"]) >= 1)


if __name__ == "__main__":
    unittest.main()
