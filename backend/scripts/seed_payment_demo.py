import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.statuses import MAPPING_ACTIVE, PARTNER_ACTIVE, PAYMENT_GATEWAY_COMPLETED, PAYMENT_PROVIDER_STRIPE
from app.extensions.db import db
from app.models.company import Company
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.services.billing_service import InvoiceService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_workflow_service import OrderWorkflowService
from app.services.payment_gateway_service import PaymentService
from app.services.scheduling import SchedulingService
from app.services.slot_generation import SlotGenerationService


def seed_payment_demo():
    if not Company.query.first():
        db.session.add(Company(company_code="DX-PAY", company_name="DxCon", tax_code="01"))
        db.session.commit()

    if Partner.query.first():
        partner = Partner.query.first()
        mapping = PartnerServiceMapping.query.filter_by(partner_id=partner.id).first()
    else:
        cat = DiagnosticCategory(category_code="BIO", name="Bio", is_active=True)
        db.session.add(cat)
        db.session.flush()
        svc = DiagnosticService(service_code="GLU", name="Glucose", category_id=cat.id, is_active=True)
        db.session.add(svc)
        partner = Partner(
            partner_code="PTR-PAY-001",
            partner_type="LABORATORY",
            legal_name="Payment Demo Lab",
            display_name="Payment Demo Lab",
            status=PARTNER_ACTIVE,
        )
        db.session.add(partner)
        db.session.flush()
        mapping = PartnerServiceMapping(
            partner_id=partner.id,
            diagnostic_service_id=svc.id,
            partner_service_code="PAY-GLU",
            partner_service_name="Glucose",
            price=180000,
            status=MAPPING_ACTIVE,
        )
        db.session.add(mapping)
        db.session.commit()
        SlotGenerationService.generate_partner_daily_slots(partner.id, days=2)

    slots = SchedulingService.list_available_slots(mapping.partner_id)
    if not slots:
        return {"payment_id": None}

    booking = MarketplaceBookingService.create_booking(
        {
            "partner_service_mapping_id": mapping.id,
            "patient_name": "Payment Demo Patient",
            "patient_phone": "0908555666",
            "requested_date": slots[0].slot_date,
        }
    )
    order = OrderWorkflowService.create_from_booking(booking.id)
    invoice = InvoiceService.create_invoice(order.id)
    payment = PaymentService.create_payment(
        {
            "invoice_id": invoice.id,
            "provider": PAYMENT_PROVIDER_STRIPE,
            "method_type": "CARD",
            "display_name": "Stripe Card",
            "last4": "4242",
        }
    )
    return {
        "invoice_id": invoice.id,
        "payment_id": payment["payment"]["id"],
        "transaction_id": payment["transaction"]["id"],
    }


def main():
    from app import create_app

    app = create_app()
    with app.app_context():
        db.create_all()
        summary = seed_payment_demo()
        print("\n=== DXCON PAYMENT GATEWAY DEMO SEED ===\n")
        for key, value in summary.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
