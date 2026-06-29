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
    BOOKING_TIMELINE_COLLECTED,
    BOOKING_TIMELINE_IN_TRANSIT,
    BOOKING_TIMELINE_LAB_RECEIVED,
    COLLECTION_COLLECTED,
    COLLECTION_RECEIVED,
    MAPPING_ACTIVE,
    ORDER_CONFIRMED,
    ORDER_LAB_RECEIVED,
    ORDER_SAMPLE_COLLECTED,
    PARTNER_ACTIVE,
)
from app.extensions.db import db
from app.models.booking_assignment import BookingAssignment
from app.models.collector_availability import CollectorAvailability
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.models.driver import Driver
from app.models.marketplace_booking_timeline import MarketplaceBookingTimeline
from app.models.order import Order
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.models.sample_collection import SampleCollection
from app.models.sample_tracking import SampleTracking
from app.services.booking_assignment import BookingAssignmentService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_lifecycle import OrderLifecycleService
from app.services.sample_collection_workflow import SampleCollectionWorkflowService
from app.services.scheduling import SchedulingService
from app.services.slot_generation import SlotGenerationService


class OrderLifecycleTestCase(unittest.TestCase):
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
            partner_code="PTR-OLC-0001",
            partner_type="LABORATORY",
            legal_name="Order Lifecycle Lab",
            display_name="Order Lifecycle Lab",
            city="Ha Noi",
            status=PARTNER_ACTIVE,
        )
        db.session.add(self.partner)
        db.session.flush()

        self.mapping = PartnerServiceMapping(
            partner_id=self.partner.id,
            diagnostic_service_id=self.service.id,
            partner_service_code="OLC-HBA1C",
            partner_service_name="HbA1c",
            price=180000,
            status=MAPPING_ACTIVE,
        )
        db.session.add(self.mapping)

        self.collector = Driver(
            driver_code="COL-OLC-001",
            full_name="Order Lifecycle Collector",
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

    def _assigned_booking(self):
        slot = SchedulingService.list_available_slots(self.partner.id)[0]
        booking = MarketplaceBookingService.create_booking(
            {
                "partner_service_mapping_id": self.mapping.id,
                "patient_name": "Lifecycle Patient",
                "patient_phone": "0908888999",
                "requested_date": slot.slot_date,
            }
        )
        BookingAssignmentService.reserve_slot_for_booking(booking.id, slot.id)
        BookingAssignmentService.assign_collector(booking.id, self.collector.id)
        return booking

    def test_create_order_from_assigned_booking(self):
        booking = self._assigned_booking()

        response = self.client.post(
            f"/api/v1/order-lifecycle/bookings/{booking.id}/create-order"
        )
        self.assertEqual(response.status_code, 201)
        order_payload = response.get_json()["order"]
        self.assertEqual(order_payload["status"], ORDER_CONFIRMED)
        self.assertEqual(order_payload["marketplace_booking_id"], booking.id)

        order = Order.query.get(order_payload["id"])
        self.assertIsNotNone(order)
        self.assertEqual(order.total_amount, 180000)

    def test_sample_collection_workflow(self):
        booking = self._assigned_booking()
        OrderLifecycleService.create_order_from_booking(booking.id)

        check_in = self.client.post(
            f"/api/v1/order-lifecycle/bookings/{booking.id}/check-in"
        )
        self.assertEqual(check_in.status_code, 200)

        collect = self.client.post(
            f"/api/v1/order-lifecycle/bookings/{booking.id}/collect",
            json={"note": "Collected at home"},
        )
        self.assertEqual(collect.status_code, 200)
        collection = SampleCollection.query.filter_by(
            marketplace_booking_id=booking.id
        ).first()
        self.assertEqual(collection.status, COLLECTION_COLLECTED)

        order = Order.query.filter_by(marketplace_booking_id=booking.id).first()
        self.assertEqual(order.status, ORDER_SAMPLE_COLLECTED)

        timeline_types = [
            item.event_type
            for item in MarketplaceBookingTimeline.query.filter_by(booking_id=booking.id).all()
        ]
        self.assertIn(BOOKING_TIMELINE_COLLECTED, timeline_types)

        dispatch = self.client.post(
            f"/api/v1/order-lifecycle/bookings/{booking.id}/dispatch"
        )
        self.assertEqual(dispatch.status_code, 200)
        self.assertIn(BOOKING_TIMELINE_IN_TRANSIT, [
            item.event_type
            for item in MarketplaceBookingTimeline.query.filter_by(booking_id=booking.id).all()
        ])

        lab_receive = self.client.post(
            f"/api/v1/order-lifecycle/bookings/{booking.id}/lab-receive"
        )
        self.assertEqual(lab_receive.status_code, 200)

        order = Order.query.filter_by(marketplace_booking_id=booking.id).first()
        self.assertEqual(order.status, ORDER_LAB_RECEIVED)
        collection = SampleCollection.query.filter_by(
            marketplace_booking_id=booking.id
        ).first()
        self.assertEqual(collection.status, COLLECTION_RECEIVED)

        sample = SampleTracking.query.filter_by(marketplace_booking_id=booking.id).first()
        self.assertIsNotNone(sample)

    def test_order_lifecycle_routes_registered(self):
        routes = {str(rule) for rule in self.app.url_map.iter_rules()}
        self.assertIn("/api/v1/order-lifecycle/orders", routes)
        self.assertIn("/order-lifecycle", routes)


if __name__ == "__main__":
    unittest.main()
