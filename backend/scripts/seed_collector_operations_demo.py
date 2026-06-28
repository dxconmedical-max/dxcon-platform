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
from app.models.transport_box import TransportBox
from app.services.booking_assignment import BookingAssignmentService
from app.services.collector_operations import CollectorOperationsService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_lifecycle import OrderLifecycleService
from app.services.scheduling import SchedulingService
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_scheduling_demo import seed_scheduling_demo


def seed_collector_operations_demo():
    seed_marketplace_demo()
    seed_scheduling_demo()

    collectors = Driver.query.filter_by(status="ACTIVE").limit(3).all()
    mappings = PartnerServiceMapping.query.limit(3).all()

    routes_created = 0
    assignments_accepted = 0
    vehicles_created = 0
    gps_pings = 0

    for index, collector in enumerate(collectors):
        vehicle = CollectorOperationsService.create_vehicle(
            collector.id,
            {
                "plate_number": f"51A-{1000 + index}",
                "vehicle_type": "MOTORBIKE",
            },
        )
        vehicles_created += 1
        CollectorOperationsService.assign_active_vehicle(collector.id, vehicle.id)

        if index >= len(mappings):
            continue

        mapping = mappings[index]
        slots = SchedulingService.list_available_slots(mapping.partner_id)
        if not slots:
            continue

        booking = MarketplaceBookingService.create_booking(
            {
                "partner_service_mapping_id": mapping.id,
                "patient_name": f"Collector Demo Patient {index + 1}",
                "patient_phone": f"0903000{index:03d}",
                "requested_date": slots[0].slot_date,
            }
        )
        BookingAssignmentService.reserve_slot_for_booking(booking.id, slots[0].id)
        assignment = BookingAssignmentService.assign_collector(booking.id, collector.id)
        OrderLifecycleService.create_order_from_booking(booking.id)
        CollectorOperationsService.accept_assignment(assignment.id, collector.id)
        assignments_accepted += 1

        box = TransportBox.query.first()
        route = CollectorOperationsService.create_route(
            collector.id,
            transport_box_id=box.id if box else None,
        )
        CollectorOperationsService.optimize_route(route.id)
        CollectorOperationsService.start_route(
            route.id,
            latitude="21.0285",
            longitude="105.8542",
        )
        routes_created += 1

        if index == 0:
            CollectorOperationsService.record_check_event(
                collector.id,
                "CHECK_IN",
                booking_id=booking.id,
                route_id=route.id,
                latitude="21.0285",
                longitude="105.8542",
            )
            CollectorOperationsService.pickup_sample(booking.id, collector.id)
            CollectorOperationsService.record_gps_ping(
                collector.id,
                latitude="21.0290",
                longitude="105.8550",
                route_id=route.id,
            )
            gps_pings += 1
            CollectorOperationsService.add_proof(
                collector.id,
                "PHOTO",
                booking_id=booking.id,
                file_name="demo.jpg",
                content_base64="demo-photo",
            )
            CollectorOperationsService.add_proof(
                collector.id,
                "SIGNATURE",
                booking_id=booking.id,
                signer_name=booking.patient_name,
                content_base64="demo-signature",
            )

    return {
        "collectors_total": len(collectors),
        "vehicles_created": vehicles_created,
        "assignments_accepted": assignments_accepted,
        "routes_created": routes_created,
        "gps_pings": gps_pings,
    }


def main():
    app = create_app()

    with app.app_context():
        db.create_all()
        summary = seed_collector_operations_demo()

        print("\n=== DXCON COLLECTOR OPERATIONS DEMO SEED ===\n")
        for key, value in summary.items():
            print(f"{key}: {value}")
        print("\nCOLLECTOR OPERATIONS DEMO SEED COMPLETE\n")


if __name__ == "__main__":
    main()
