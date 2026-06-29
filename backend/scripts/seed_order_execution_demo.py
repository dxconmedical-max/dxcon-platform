import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.driver import Driver
from app.models.partner_service_mapping import PartnerServiceMapping
from app.services.booking_assignment import BookingAssignmentService
from app.services.incident_service import IncidentService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_lifecycle import OrderLifecycleService
from app.services.order_workflow_service import OrderWorkflowService
from app.services.sample_tracking_service import SampleTrackingService
from app.services.scheduling import SchedulingService
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_scheduling_demo import seed_scheduling_demo


def seed_order_execution_demo(limit=2):
    seed_marketplace_demo()
    seed_scheduling_demo()

    mappings = PartnerServiceMapping.query.limit(limit).all()
    collector = Driver.query.filter_by(status="ACTIVE").first()

    orders_created = 0
    completed_orders = 0
    labels_created = 0
    incidents_logged = 0

    for index, mapping in enumerate(mappings):
        slots = SchedulingService.list_available_slots(mapping.partner_id)
        if not slots:
            continue

        booking = MarketplaceBookingService.create_booking(
            {
                "partner_service_mapping_id": mapping.id,
                "patient_name": f"Execution Demo Patient {index + 1}",
                "patient_phone": f"0905000{index:03d}",
                "requested_date": slots[0].slot_date,
            }
        )
        BookingAssignmentService.reserve_slot_for_booking(booking.id, slots[0].id)
        if collector:
            BookingAssignmentService.assign_collector(booking.id, collector.id)
        OrderLifecycleService.create_order_from_booking(booking.id)

        order = OrderWorkflowService.create_from_booking(booking.id)
        orders_created += 1

        OrderWorkflowService.advance_booking_workflow(order.id)
        order, _executed = OrderWorkflowService.run_demo_execution_flow(order.id)
        if order.status == "COMPLETED":
            completed_orders += 1

        SampleTrackingService.create_label(order.id, mark_printed=True)
        labels_created += 1

        if index == 0:
            IncidentService.log_incident(
                order.id,
                incident_type="CHAIN_OF_CUSTODY",
                description="Demo incident logged during seed",
            )
            incidents_logged += 1

    return {
        "orders_created": orders_created,
        "completed_orders": completed_orders,
        "labels_created": labels_created,
        "incidents_logged": incidents_logged,
    }


def main():
    app = create_app()

    with app.app_context():
        db.create_all()
        summary = seed_order_execution_demo()

        print("\n=== DXCON ORDER EXECUTION DEMO SEED ===\n")
        for key, value in summary.items():
            print(f"{key}: {value}")
        print("\nORDER EXECUTION DEMO SEED COMPLETE\n")


if __name__ == "__main__":
    main()
