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
from app.services.billing_service import BillingService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_workflow_service import OrderWorkflowService
from app.services.reporting_service import ExecutiveDashboardService, ReportingService
from app.services.scheduling import SchedulingService
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_scheduling_demo import seed_scheduling_demo


def seed_reporting_demo():
    if not Company.query.first():
        db.session.add(Company(company_code="DX-RPT", company_name="DxCon", tax_code="01"))
        db.session.commit()

    seed_marketplace_demo()
    seed_scheduling_demo()
    mapping = PartnerServiceMapping.query.first()
    if not mapping:
        return {"orders_created": 0}

    slots = SchedulingService.list_available_slots(mapping.partner_id)
    if not slots:
        return {"orders_created": 0}

    booking = MarketplaceBookingService.create_booking(
        {
            "partner_service_mapping_id": mapping.id,
            "patient_name": "Reporting Demo Patient",
            "patient_phone": "0908000002",
            "requested_date": slots[0].slot_date,
        }
    )
    order = OrderWorkflowService.create_from_booking(booking.id)
    BillingService.create_invoice_from_medical_order(order.id)
    ReportingService.get_operations_report()
    ExecutiveDashboardService.get_dashboard()
    return {"orders_created": 1, "partner_id": mapping.partner_id}


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        summary = seed_reporting_demo()
        print("\n=== DXCON REPORTING DEMO SEED ===\n")
        for k, v in summary.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
