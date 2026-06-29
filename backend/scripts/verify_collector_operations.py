import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import ASSIGNMENT_ACCEPTED, ROUTE_IN_PROGRESS
from app.extensions.db import db
from app.models.booking_assignment import BookingAssignment
from app.models.collector_operation_timeline import CollectorOperationTimeline
from app.models.driver import Driver
from app.models.transport_box import TransportBox
from app.services.booking_assignment import BookingAssignmentService
from app.services.collector_operations import CollectorOperationsService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_lifecycle import OrderLifecycleService
from app.services.scheduling import SchedulingService
from scripts.seed_collector_operations_demo import seed_collector_operations_demo
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_scheduling_demo import seed_scheduling_demo


def verify_models_import():
    models = [
        BookingAssignment,
        CollectorOperationTimeline,
        TransportBox,
        Driver,
    ]
    for model in models:
        assert model.__tablename__
    print("OK: collector operations models import")


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/collector-operations/collectors/<collector_id>/profile",
        "/api/v1/collector-operations/collectors/<collector_id>/jobs",
        "/api/v1/collector-operations/collectors/<collector_id>/routes",
        "/api/v1/collector-operations/routes/<route_id>/optimize",
        "/api/v1/collector-operations/collectors/<collector_id>/gps",
        "/api/v1/collector-operations/qr/scan",
        "/api/v1/collector-operations/handovers",
        "/api/v1/collector-operations/proofs",
        "/api/v1/collector-operations/collectors/<collector_id>/offline/sync",
        "/api/v1/collector-operations/collectors/<collector_id>/dashboard",
        "/api/v1/collector-operations/supervisor/dashboard",
        "/collector-operations",
        "/collector-operations/supervisor",
    ]

    for route in required:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            return False

    collector_page = any(
        rule.rule.startswith("/collector-operations/collectors/<collector_id>")
        for rule in app.url_map.iter_rules()
    )
    if collector_page:
        print("OK: /collector-operations/collectors/<collector_id>")
    else:
        print("MISSING: collector dashboard page")
        return False

    return True


def verify_seed_and_flow():
    with app.app_context():
        db.create_all()
        seed_marketplace_demo()
        seed_scheduling_demo()
        summary = seed_collector_operations_demo()

        if summary["collectors_total"] < 1:
            print("MISSING: demo collectors required")
            return False
        print("OK: collector operations demo seed")

        collector = Driver.query.filter_by(status="ACTIVE").first()
        assignment = BookingAssignment.query.filter_by(
            collector_id=collector.id,
            assignment_status=ASSIGNMENT_ACCEPTED,
        ).first()

        if not assignment:
            from app.models.partner_service_mapping import PartnerServiceMapping

            mapping = PartnerServiceMapping.query.first()
            slots = SchedulingService.list_available_slots(mapping.partner_id)
            booking = MarketplaceBookingService.create_booking(
                {
                    "partner_service_mapping_id": mapping.id,
                    "patient_name": "Collector Ops Verify Patient",
                    "patient_phone": "0900000100",
                    "requested_date": slots[0].slot_date,
                }
            )
            BookingAssignmentService.reserve_slot_for_booking(booking.id, slots[0].id)
            BookingAssignmentService.assign_collector(booking.id, collector.id)
            OrderLifecycleService.create_order_from_booking(booking.id)
            assignment = BookingAssignment.query.filter_by(booking_id=booking.id).first()
            CollectorOperationsService.accept_assignment(assignment.id, collector.id)

        route = CollectorOperationsService.create_route(collector.id)
        CollectorOperationsService.optimize_route(route.id)
        route = CollectorOperationsService.start_route(route.id, latitude="21.02", longitude="105.85")

        if route.status != ROUTE_IN_PROGRESS:
            print("MISSING: route in progress after start")
            return False
        print("OK: route assignment and optimization")

        CollectorOperationsService.record_gps_ping(
            collector.id,
            latitude="21.03",
            longitude="105.86",
            route_id=route.id,
        )
        print("OK: gps tracking")

        timeline_count = CollectorOperationTimeline.query.filter_by(
            collector_id=collector.id
        ).count()
        if timeline_count < 1:
            print("MISSING: collector timeline events")
            return False
        print("OK: timeline events")

        dashboard = CollectorOperationsService.collector_dashboard(collector.id)
        supervisor = CollectorOperationsService.supervisor_dashboard()
        if not dashboard or not supervisor:
            print("MISSING: dashboards")
            return False
        print("OK: collector and supervisor dashboards")
        return True


app = create_app()

print("\n=== DXCON COLLECTOR OPERATIONS VERIFY ===\n")

errors = 0

try:
    verify_models_import()
except Exception as exc:
    print("MISSING: collector operations models import", exc)
    errors += 1

if not verify_routes(app):
    errors += 1

if not verify_seed_and_flow():
    errors += 1

if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)

print("\nCOLLECTOR OPERATIONS VERIFY PASSED\n")
