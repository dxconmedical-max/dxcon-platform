import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.company import Company
from app.models.partner_service_mapping import PartnerServiceMapping
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_workflow_service import OrderWorkflowService
from app.services.result_gateway_service import ResultApprovalService, ResultReleaseService, ResultReviewService
from app.services.scheduling import SchedulingService
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_results_demo import seed_results_demo
from scripts.seed_scheduling_demo import seed_scheduling_demo


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/results",
        "/api/v1/results/upload",
        "/api/v1/results/manual",
        "/api/v1/results/<result_id>",
        "/api/v1/results/<result_id>/review",
        "/api/v1/results/<result_id>/approve",
        "/api/v1/results/<result_id>/release",
        "/api/v1/results/<result_id>/timeline",
        "/results",
        "/results/upload",
        "/results/<result_id>",
    ]
    for route in required:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            return False
    return True


def verify_seed_and_flow():
    with app.app_context():
        db.create_all()
        if not Company.query.first():
            db.session.add(Company(company_code="DX-RG", company_name="DxCon", tax_code="01"))
            db.session.commit()
        seed_marketplace_demo()
        seed_scheduling_demo()
        summary = seed_results_demo()
        if summary["results_created"] < 1:
            print("MISSING: results demo seed")
            return False
        print("OK: results demo seed")

        mapping = PartnerServiceMapping.query.first()
        slots = SchedulingService.list_available_slots(mapping.partner_id)
        booking = MarketplaceBookingService.create_booking(
            {
                "partner_service_mapping_id": mapping.id,
                "patient_name": "Verify Patient",
                "patient_phone": "0908000003",
                "requested_date": slots[0].slot_date,
            }
        )
        order = OrderWorkflowService.create_from_booking(booking.id)
        from app.services.result_gateway_service import ResultUploadService, ResultValidationService

        result = ResultUploadService.create_manual(
            {
                "medical_order_id": order.id,
                "items": [{"test_name": "TSH", "result_value": "2.1", "reference_range": "0.4-4.0"}],
            }
        )
        ResultValidationService.validate(result.id)
        ResultReviewService.submit_review(result.id, {"comments": "Review ok"})
        ResultApprovalService.approve(result.id, {"comments": "Approved"})
        ResultReleaseService.release(result.id, {})
        print("OK: result gateway workflow")
        return True


app = create_app()
print("\n=== DXCON RESULT GATEWAY VERIFY ===\n")
errors = 0
if not verify_routes(app):
    errors += 1
if not verify_seed_and_flow():
    errors += 1
if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nRESULT GATEWAY VERIFY PASSED\n")
