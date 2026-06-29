import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.booking_assignment import BookingAssignment
from app.models.collector_availability import CollectorAvailability
from app.models.driver import Driver
from app.models.marketplace_booking import MarketplaceBooking
from app.models.partner_capacity import PartnerCapacity
from app.models.scheduling_calendar import SchedulingCalendar
from app.models.scheduling_slot import SchedulingSlot
from app.services.booking_assignment import BookingAssignmentService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.scheduling import SchedulingService
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_scheduling_demo import seed_scheduling_demo


def verify_models_import():
    models = [
        SchedulingCalendar,
        SchedulingSlot,
        PartnerCapacity,
        CollectorAvailability,
        BookingAssignment,
    ]
    for model in models:
        assert model.__tablename__
    print("OK: scheduling models import")


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/scheduling/partners/<partner_id>/slots",
        "/api/v1/scheduling/partners/<partner_id>/generate-slots",
        "/api/v1/scheduling/bookings/<booking_id>/reserve-slot",
        "/api/v1/scheduling/bookings/<booking_id>/assign-collector",
        "/api/v1/scheduling/collectors/availability",
        "/scheduling",
        "/scheduling/collectors",
    ]

    for route in required:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            return False

    partner_page = any(
        rule.rule.startswith("/scheduling/partners/<partner_id>")
        for rule in app.url_map.iter_rules()
    )
    if partner_page:
        print("OK: /scheduling/partners/<partner_id>")
    else:
        print("MISSING: partner scheduling page")
        return False

    return True


def verify_seed_and_flow():
    with app.app_context():
        db.create_all()
        seed_marketplace_demo()
        summary = seed_scheduling_demo()

        if summary["partners_total"] < 1:
            print("MISSING: demo partners required for scheduling seed")
            return False
        print("OK: scheduling demo seed")

        partner = MarketplaceBooking.query.first()
        if not partner:
            partner_id = db.session.query(MarketplaceBooking.partner_id).first()
            if partner_id:
                partner_id = partner_id[0]
            else:
                from app.models.partner_service_mapping import PartnerServiceMapping
                mapping = PartnerServiceMapping.query.first()
                partner_id = mapping.partner_id if mapping else None
        else:
            partner_id = partner.partner_id

        if not partner_id:
            print("MISSING: partner required for slot query")
            return False

        slots = SchedulingService.list_available_slots(partner_id)
        if not slots:
            print("MISSING: available slots after seed")
            return False
        print("OK: available slots query")

        booking = MarketplaceBooking.query.first()
        if not booking:
            from app.models.partner_service_mapping import PartnerServiceMapping
            mapping = PartnerServiceMapping.query.first()
            if not mapping:
                print("MISSING: mapping required to create demo booking")
                return False
            booking = MarketplaceBookingService.create_booking(
                {
                    "partner_service_mapping_id": mapping.id,
                    "patient_name": "Scheduling Verify Patient",
                    "patient_phone": "0900000001",
                    "requested_date": slots[0].slot_date,
                }
            )

        slot = slots[0]
        BookingAssignmentService.reserve_slot_for_booking(booking.id, slot.id)
        print("OK: slot reserved for booking")

        collector = Driver.query.filter_by(status="ACTIVE").first()
        availability = CollectorAvailability.query.first()
        if collector and availability:
            BookingAssignmentService.assign_collector(booking.id, collector.id)
            assignment = BookingAssignment.query.filter_by(booking_id=booking.id).first()
            if not assignment:
                print("MISSING: booking assignment after assign-collector")
                return False
            print("OK: booking assigned to collector")
        else:
            print("OK: booking assignment skipped (no demo collector availability)")

        return True


app = create_app()

print("\n=== DXCON SCHEDULING VERIFY ===\n")

errors = 0

try:
    verify_models_import()
except Exception as exc:
    print("MISSING: scheduling models import", exc)
    errors += 1

if not verify_routes(app):
    errors += 1

if not verify_seed_and_flow():
    errors += 1

if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)

print("\nSCHEDULING VERIFY PASSED\n")
