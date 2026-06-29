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
from app.services.interpretation_engine_service import InterpretationEngine
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_workflow_service import OrderWorkflowService
from app.services.result_gateway_service import ResultUploadService, ResultValidationService
from app.services.scheduling import SchedulingService
from scripts.seed_interpretation_demo import seed_interpretation_demo
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_scheduling_demo import seed_scheduling_demo


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/interpretation/rules",
        "/api/v1/interpretation/run",
        "/api/v1/interpretation/<result_id>",
        "/api/v1/reference-ranges",
        "/interpretation",
        "/reference-ranges",
        "/critical-values",
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
            db.session.add(Company(company_code="DX-INT", company_name="DxCon", tax_code="01"))
            db.session.commit()
        seed_marketplace_demo()
        seed_scheduling_demo()
        summary = seed_interpretation_demo()
        if summary.get("already_seeded"):
            print("OK: interpretation demo already present")
        else:
            print("OK: interpretation demo seed")

        mapping = PartnerServiceMapping.query.first()
        slots = SchedulingService.list_available_slots(mapping.partner_id)
        booking = MarketplaceBookingService.create_booking(
            {
                "partner_service_mapping_id": mapping.id,
                "patient_name": "Verify Interpretation",
                "patient_phone": "0908000005",
                "requested_date": slots[0].slot_date,
            }
        )
        order = OrderWorkflowService.create_from_booking(booking.id)
        lab_result = ResultUploadService.create_manual(
            {
                "medical_order_id": order.id,
                "items": [
                    {
                        "test_code": "GLU",
                        "test_name": "Glucose",
                        "result_value": "8.0",
                        "unit": "mmol/L",
                    }
                ],
            }
        )
        ResultValidationService.validate(lab_result.id)
        rows = InterpretationEngine.run(lab_result.id, patient_age=30, patient_sex="F")
        if not rows:
            print("MISSING: interpretation rows")
            return False
        print("OK: interpretation engine run")
        return True


app = create_app()
print("\n=== DXCON INTERPRETATION VERIFY ===\n")
errors = 0
if not verify_routes(app):
    errors += 1
if not verify_seed_and_flow():
    errors += 1
if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nINTERPRETATION VERIFY PASSED\n")
