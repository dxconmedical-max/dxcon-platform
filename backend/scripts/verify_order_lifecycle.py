import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import COLLECTION_RECEIVED, ORDER_LAB_RECEIVED
from app.extensions.db import db
from app.models.marketplace_booking import MarketplaceBooking
from app.models.order import Order
from app.models.sample_collection import SampleCollection
from app.services.booking_assignment import BookingAssignmentService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_lifecycle import OrderLifecycleService
from app.services.sample_collection_workflow import SampleCollectionWorkflowService
from app.services.scheduling import SchedulingService
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_order_lifecycle_demo import seed_order_lifecycle_demo
from scripts.seed_scheduling_demo import seed_scheduling_demo


def verify_models_import():
    models = [
        Order,
        SampleCollection,
        MarketplaceBooking,
    ]
    for model in models:
        assert model.__tablename__
    print("OK: order lifecycle models import")


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/order-lifecycle/orders",
        "/api/v1/order-lifecycle/bookings/<booking_id>/create-order",
        "/api/v1/order-lifecycle/bookings/<booking_id>/check-in",
        "/api/v1/order-lifecycle/bookings/<booking_id>/collect",
        "/api/v1/order-lifecycle/bookings/<booking_id>/dispatch",
        "/api/v1/order-lifecycle/bookings/<booking_id>/lab-receive",
        "/order-lifecycle",
    ]

    for route in required:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            return False

    booking_page = any(
        rule.rule.startswith("/order-lifecycle/bookings/<booking_id>")
        for rule in app.url_map.iter_rules()
    )
    if booking_page:
        print("OK: /order-lifecycle/bookings/<booking_id>")
    else:
        print("MISSING: order lifecycle booking page")
        return False

    return True


def verify_seed_and_flow():
    with app.app_context():
        db.create_all()
        seed_marketplace_demo()
        seed_scheduling_demo()
        summary = seed_order_lifecycle_demo()

        if summary["bookings_processed"] < 1:
            print("MISSING: demo bookings required for order lifecycle seed")
            return False
        print("OK: order lifecycle demo seed")

        booking = MarketplaceBooking.query.filter(
            MarketplaceBooking.status == "ASSIGNED"
        ).first()
        if not booking:
            from app.models.partner_service_mapping import PartnerServiceMapping
            from app.models.driver import Driver

            mapping = PartnerServiceMapping.query.first()
            slots = SchedulingService.list_available_slots(mapping.partner_id)
            if not mapping or not slots:
                print("MISSING: mapping and slots required for verify flow")
                return False

            booking = MarketplaceBookingService.create_booking(
                {
                    "partner_service_mapping_id": mapping.id,
                    "patient_name": "Order Lifecycle Verify Patient",
                    "patient_phone": "0900000099",
                    "requested_date": slots[0].slot_date,
                }
            )
            BookingAssignmentService.reserve_slot_for_booking(booking.id, slots[0].id)
            collector = Driver.query.filter_by(status="ACTIVE").first()
            if collector:
                BookingAssignmentService.assign_collector(booking.id, collector.id)

        order = OrderLifecycleService.create_order_from_booking(booking.id)
        if not order:
            print("MISSING: order after create-order flow")
            return False
        print("OK: order created from booking")

        collection = SampleCollection.query.filter_by(
            marketplace_booking_id=booking.id
        ).first()
        if collection and collection.status == COLLECTION_RECEIVED:
            order = Order.query.filter_by(marketplace_booking_id=booking.id).first()
            if order and order.status == ORDER_LAB_RECEIVED:
                print("OK: full sample collection workflow")
                return True

        SampleCollectionWorkflowService.check_in_collection(booking.id)
        SampleCollectionWorkflowService.record_collection(booking.id)
        SampleCollectionWorkflowService.dispatch_sample(booking.id)
        SampleCollectionWorkflowService.receive_at_lab(booking.id)

        order = Order.query.filter_by(marketplace_booking_id=booking.id).first()
        collection = SampleCollection.query.filter_by(
            marketplace_booking_id=booking.id
        ).first()

        if not order or order.status != ORDER_LAB_RECEIVED:
            print("MISSING: order lab received status")
            return False
        if not collection:
            print("MISSING: sample collection record")
            return False

        print("OK: full sample collection workflow")
        return True


app = create_app()

print("\n=== DXCON ORDER LIFECYCLE VERIFY ===\n")

errors = 0

try:
    verify_models_import()
except Exception as exc:
    print("MISSING: order lifecycle models import", exc)
    errors += 1

if not verify_routes(app):
    errors += 1

if not verify_seed_and_flow():
    errors += 1

if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)

print("\nORDER LIFECYCLE VERIFY PASSED\n")
