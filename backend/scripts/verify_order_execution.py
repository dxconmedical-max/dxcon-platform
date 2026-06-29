import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import MEDICAL_ORDER_COMPLETED
from app.extensions.db import db
from app.models.medical_order import MedicalOrder
from app.models.medical_order_event import MedicalOrderEvent
from app.models.sample_label import SampleLabel
from app.services.booking_assignment import BookingAssignmentService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_lifecycle import OrderLifecycleService
from app.services.order_workflow_service import OrderWorkflowService
from app.services.scheduling import SchedulingService
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_order_execution_demo import seed_order_execution_demo
from scripts.seed_scheduling_demo import seed_scheduling_demo


def verify_models_import():
    models = [MedicalOrder, MedicalOrderEvent, SampleLabel]
    for model in models:
        assert model.__tablename__
    print("OK: order execution models import")


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/order-execution/orders",
        "/api/v1/order-execution/orders/<order_id>",
        "/api/v1/order-execution/orders/<order_id>/timeline",
        "/api/v1/order-execution/orders/<order_id>/barcode",
        "/api/v1/order-execution/orders/<order_id>/label",
        "/api/v1/order-execution/orders/<order_id>/incident",
        "/api/v1/order-execution/orders/<order_id>/cancel",
        "/api/v1/order-execution/orders/<order_id>/refund",
        "/api/v1/order-execution/orders/<order_id>/recollect",
        "/order-execution",
    ]

    for route in required:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            return False

    detail_page = any(
        rule.rule.startswith("/order-execution/orders/<order_id>")
        for rule in app.url_map.iter_rules()
    )
    if detail_page:
        print("OK: /order-execution/orders/<order_id>")
    else:
        print("MISSING: order execution detail page")
        return False

    return True


def verify_seed_and_flow():
    with app.app_context():
        db.create_all()
        seed_marketplace_demo()
        seed_scheduling_demo()
        summary = seed_order_execution_demo()

        if summary["orders_created"] < 1:
            print("MISSING: demo medical orders required")
            return False
        print("OK: order execution demo seed")

        order = MedicalOrder.query.first()
        if not order:
            print("MISSING: medical order after seed")
            return False

        if order.status != MEDICAL_ORDER_COMPLETED:
            print("MISSING: completed demo order status")
            return False
        print("OK: full medical order workflow")

        timeline = MedicalOrderEvent.query.filter_by(medical_order_id=order.id).count()
        if timeline < 5:
            print("MISSING: medical order timeline events")
            return False
        print("OK: audit timeline")

        labels = SampleLabel.query.filter_by(medical_order_id=order.id).count()
        if labels < 1:
            print("MISSING: sample labels")
            return False
        print("OK: label generation")

        barcode = OrderWorkflowService.get_barcode(order.id)
        if not barcode.get("barcode_value"):
            print("MISSING: order barcode")
            return False
        print("OK: barcode and QR generation")
        return True


app = create_app()

print("\n=== DXCON ORDER EXECUTION VERIFY ===\n")

errors = 0

try:
    verify_models_import()
except Exception as exc:
    print("MISSING: order execution models import", exc)
    errors += 1

if not verify_routes(app):
    errors += 1

if not verify_seed_and_flow():
    errors += 1

if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)

print("\nORDER EXECUTION VERIFY PASSED\n")
