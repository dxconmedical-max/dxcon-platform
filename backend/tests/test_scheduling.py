import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
    ASSIGNMENT_ASSIGNED,
    BOOKING_TIMELINE_COLLECTOR_ASSIGNED,
    BOOKING_TIMELINE_SLOT_RESERVED,
    MAPPING_ACTIVE,
    PARTNER_ACTIVE,
)
from app.extensions.db import db
from app.models.booking_assignment import BookingAssignment
from app.models.collector_availability import CollectorAvailability
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.models.driver import Driver
from app.models.marketplace_booking_timeline import MarketplaceBookingTimeline
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.models.scheduling_slot import SchedulingSlot
from app.services.booking_assignment import BookingAssignmentService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.scheduling import SchedulingService
from app.services.slot_generation import SlotGenerationService


class SchedulingEngineTestCase(unittest.TestCase):
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
            category_id=self.category.id,
            estimated_turnaround_hours=24,
            is_active=True,
        )
        db.session.add(self.service)

        self.partner = Partner(
            partner_code="PTR-SCH-0001",
            partner_type="LABORATORY",
            legal_name="Scheduling Lab",
            display_name="Scheduling Lab",
            city="Ha Noi",
            status=PARTNER_ACTIVE,
        )
        db.session.add(self.partner)
        db.session.flush()

        self.mapping = PartnerServiceMapping(
            partner_id=self.partner.id,
            diagnostic_service_id=self.service.id,
            partner_service_code="SCH-HBA1C",
            partner_service_name="HbA1c",
            price=180000,
            status=MAPPING_ACTIVE,
        )
        db.session.add(self.mapping)

        self.collector = Driver(
            driver_code="COL-TEST-001",
            full_name="Test Collector",
            status="ACTIVE",
        )
        db.session.add(self.collector)
        db.session.commit()

        SlotGenerationService.generate_partner_daily_slots(self.partner.id, days=2)
        SlotGenerationService.generate_collector_availability(
            self.collector.id,
            days=2,
            city="Ha Noi",
            district="Cau Giay",
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_list_available_slots(self):
        slots = SchedulingService.list_available_slots(self.partner.id)
        self.assertGreater(len(slots), 0)

        response = self.client.get(f"/api/v1/scheduling/partners/{self.partner.id}/slots")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.get_json()["count"], 0)

    def test_create_booking_with_slot_id(self):
        slot = SchedulingService.list_available_slots(self.partner.id)[0]

        response = self.client.post(
            "/api/v1/marketplace/bookings",
            json={
                "partner_service_mapping_id": self.mapping.id,
                "patient_name": "Slot Patient",
                "patient_phone": "0901234567",
                "slot_id": slot.id,
            },
        )
        self.assertEqual(response.status_code, 201)
        booking = response.get_json()["booking"]
        self.assertEqual(booking["scheduled_slot_id"], slot.id)

        timeline = MarketplaceBookingTimeline.query.filter_by(
            booking_id=booking["id"],
            event_type=BOOKING_TIMELINE_SLOT_RESERVED,
        ).first()
        self.assertIsNotNone(timeline)

    def test_reserve_slot_and_assign_collector(self):
        booking = MarketplaceBookingService.create_booking(
            {
                "partner_service_mapping_id": self.mapping.id,
                "patient_name": "Assign Patient",
                "patient_phone": "0902222333",
                "requested_date": SchedulingService.list_available_slots(self.partner.id)[0].slot_date,
            }
        )
        slot = SchedulingService.list_available_slots(self.partner.id)[0]

        reserve_response = self.client.post(
            f"/api/v1/scheduling/bookings/{booking.id}/reserve-slot",
            json={"slot_id": slot.id},
        )
        self.assertEqual(reserve_response.status_code, 200)

        assign_response = self.client.post(
            f"/api/v1/scheduling/bookings/{booking.id}/assign-collector",
            json={"collector_id": self.collector.id},
        )
        self.assertEqual(assign_response.status_code, 200)

        assignment = BookingAssignment.query.filter_by(booking_id=booking.id).first()
        self.assertEqual(assignment.assignment_status, ASSIGNMENT_ASSIGNED)

        timeline_types = [
            item.event_type
            for item in MarketplaceBookingTimeline.query.filter_by(booking_id=booking.id).all()
        ]
        self.assertIn(BOOKING_TIMELINE_COLLECTOR_ASSIGNED, timeline_types)


if __name__ == "__main__":
    unittest.main()
