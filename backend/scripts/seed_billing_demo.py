import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.company import Company
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.services.billing_service import BillingService
from app.services.commission_service import CommissionService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_workflow_service import OrderWorkflowService
from app.services.scheduling import SchedulingService
from app.services.settlement_service import SettlementService
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_scheduling_demo import seed_scheduling_demo


def seed_billing_demo():
    if not Company.query.first():
        db.session.add(
            Company(
                company_code="DXCON-BILL",
                company_name="DxCon Billing Co",
                tax_code="0100000001",
            )
        )
        db.session.commit()

    seed_marketplace_demo()
    seed_scheduling_demo()
    mapping = PartnerServiceMapping.query.first()
    if not mapping:
        return {"invoices_created": 0, "settlements_created": 0}

    slots = SchedulingService.list_available_slots(mapping.partner_id)
    if not slots:
        return {"invoices_created": 0, "settlements_created": 0}

    booking = MarketplaceBookingService.create_booking(
        {
            "partner_service_mapping_id": mapping.id,
            "patient_name": "Billing Demo Patient",
            "patient_phone": "0907000001",
            "requested_date": slots[0].slot_date,
        }
    )
    order = OrderWorkflowService.create_from_booking(booking.id)
    invoice = BillingService.create_invoice_from_medical_order(order.id)
    BillingService.record_payment(invoice.id)
    CommissionService.calculate_for_invoice(invoice.id, partner_id=mapping.partner_id)
    settlement = SettlementService.create_settlement(mapping.partner_id)
    SettlementService.finalize_settlement(settlement.id)

    return {
        "invoices_created": 1,
        "settlements_created": 1,
        "partner_id": mapping.partner_id,
    }


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        summary = seed_billing_demo()
        print("\n=== DXCON BILLING DEMO SEED ===\n")
        for key, value in summary.items():
            print(f"{key}: {value}")
        print("\nBILLING DEMO SEED COMPLETE\n")


if __name__ == "__main__":
    main()
