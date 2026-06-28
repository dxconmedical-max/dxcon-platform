import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import MARKETPLACE_BOOKING_ASSIGNED
from app.extensions.db import db
from app.models.driver import Driver
from app.models.marketplace_booking import MarketplaceBooking
from app.models.partner_service_mapping import PartnerServiceMapping
from app.services.booking_assignment import BookingAssignmentService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_lifecycle import OrderLifecycleService
from app.services.sample_collection_workflow import SampleCollectionWorkflowService
from app.services.scheduling import SchedulingService
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_scheduling_demo import seed_scheduling_demo


def _ensure_assigned_bookings(limit=3):
    bookings = []
    mappings = PartnerServiceMapping.query.limit(limit).all()

    for index, mapping in enumerate(mappings):
        slots = SchedulingService.list_available_slots(mapping.partner_id)
        if not slots:
            continue

        slot = slots[0]
        booking = MarketplaceBookingService.create_booking(
            {
                "partner_service_mapping_id": mapping.id,
                "patient_name": f"Order Lifecycle Demo Patient {index + 1}",
                "patient_phone": f"0901000{index:03d}",
                "requested_date": slot.slot_date,
            }
        )
        BookingAssignmentService.reserve_slot_for_booking(booking.id, slot.id)

        collector = Driver.query.filter_by(status="ACTIVE").first()
        if collector:
            BookingAssignmentService.assign_collector(booking.id, collector.id)

        if booking.status == MARKETPLACE_BOOKING_ASSIGNED:
            bookings.append(booking)

    return bookings


def seed_order_lifecycle_demo(limit=3):
    seed_marketplace_demo()
    seed_scheduling_demo()

    bookings = _ensure_assigned_bookings(limit=limit)
    if not bookings:
        existing = MarketplaceBooking.query.filter_by(
            status=MARKETPLACE_BOOKING_ASSIGNED
        ).limit(limit).all()
        bookings = existing

    processed = 0
    orders_created = 0
    collections_completed = 0

    for index, booking in enumerate(bookings):
        try:
            order = OrderLifecycleService.create_order_from_booking(booking.id)
            orders_created += 1
        except Exception:
            continue

        if index == 0 and order:
            SampleCollectionWorkflowService.check_in_collection(booking.id)
            SampleCollectionWorkflowService.record_collection(booking.id)
            SampleCollectionWorkflowService.dispatch_sample(booking.id)
            SampleCollectionWorkflowService.receive_at_lab(booking.id)
            collections_completed += 1

        processed += 1

    return {
        "bookings_processed": processed,
        "orders_created": orders_created,
        "collections_completed": collections_completed,
    }


def main():
    app = create_app()

    with app.app_context():
        db.create_all()
        summary = seed_order_lifecycle_demo()

        print("\n=== DXCON ORDER LIFECYCLE DEMO SEED ===\n")
        for key, value in summary.items():
            print(f"{key}: {value}")
        print("\nORDER LIFECYCLE DEMO SEED COMPLETE\n")


if __name__ == "__main__":
    main()
