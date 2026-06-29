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
from app.services.result_gateway_service import (
    ResultApprovalService,
    ResultReleaseService,
    ResultReviewService,
    ResultUploadService,
    ResultValidationService,
)
from app.services.scheduling import SchedulingService
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_scheduling_demo import seed_scheduling_demo


def seed_results_demo():
    if not Company.query.first():
        db.session.add(Company(company_code="DX-RG", company_name="DxCon", tax_code="01"))
        db.session.commit()

    seed_marketplace_demo()
    seed_scheduling_demo()
    mapping = PartnerServiceMapping.query.first()
    if not mapping:
        return {"results_created": 0}

    slots = SchedulingService.list_available_slots(mapping.partner_id)
    if not slots:
        return {"results_created": 0}

    booking = MarketplaceBookingService.create_booking(
        {
            "partner_service_mapping_id": mapping.id,
            "patient_name": "Results Demo Patient",
            "patient_phone": "0908000004",
            "requested_date": slots[0].slot_date,
        }
    )
    order = OrderWorkflowService.create_from_booking(booking.id)

    manual = ResultUploadService.create_manual(
        {
            "medical_order_id": order.id,
            "summary": "Demo manual result",
            "items": [
                {
                    "test_code": "GLU",
                    "test_name": "Glucose",
                    "result_value": "5.0",
                    "unit": "mmol/L",
                    "reference_range": "3.9-6.1",
                }
            ],
            "attachments": [
                {
                    "file_name": "demo-result.pdf",
                    "file_path": "/uploads/results/demo-result.pdf",
                    "mime_type": "application/pdf",
                }
            ],
        }
    )
    ResultValidationService.validate(manual.id)
    ResultReviewService.submit_review(manual.id, {"comments": "Demo review"})
    ResultApprovalService.approve(manual.id, {"comments": "Demo approved"})
    ResultReleaseService.release(manual.id, {"release_channel": "PORTAL"})

    analyzer = ResultUploadService.upload_analyzer(
        {
            "medical_order_id": order.id,
            "analyzer_payload": {"instrument": "DX-200", "run_id": "RUN-001"},
            "items": [
                {
                    "test_code": "HBA1C",
                    "test_name": "HbA1c",
                    "result_value": "5.6",
                    "unit": "%",
                    "reference_range": "4.0-6.0",
                }
            ],
        }
    )
    ResultValidationService.validate(analyzer.id)

    return {
        "results_created": 2,
        "released_results": 1,
        "medical_order_id": order.id,
    }


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        summary = seed_results_demo()
        print("\n=== DXCON RESULT GATEWAY DEMO SEED ===\n")
        for key, value in summary.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
