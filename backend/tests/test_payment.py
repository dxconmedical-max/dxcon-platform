import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
    MAPPING_ACTIVE,
    PARTNER_ACTIVE,
    PAYMENT_GATEWAY_COMPLETED,
    PAYMENT_GATEWAY_REFUNDED,
    PAYMENT_PROVIDER_MOMO,
    PAYMENT_PROVIDER_STRIPE,
    PAYMENT_PROVIDER_VNPAY,
)
from app.extensions.db import db
from app.models.company import Company
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.models.payment_transaction import PaymentTransaction
from app.models.payment_webhook import PaymentWebhook
from app.services.billing_service import InvoiceService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_workflow_service import OrderWorkflowService
from app.services.scheduling import SchedulingService
from app.services.slot_generation import SlotGenerationService
from scripts.seed_payment_demo import seed_payment_demo


class PaymentGatewayTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        db.session.add(Company(company_code="DX", company_name="DxCon", tax_code="01"))
        cat = DiagnosticCategory(category_code="BIO", name="Bio", is_active=True)
        db.session.add(cat)
        db.session.flush()
        svc = DiagnosticService(service_code="GLU", name="Glucose", category_id=cat.id, is_active=True)
        db.session.add(svc)
        self.partner = Partner(
            partner_code="PTR-PAY-TST",
            partner_type="LABORATORY",
            legal_name="Payment Test Lab",
            display_name="Payment Test Lab",
            status=PARTNER_ACTIVE,
        )
        db.session.add(self.partner)
        db.session.flush()
        self.mapping = PartnerServiceMapping(
            partner_id=self.partner.id,
            diagnostic_service_id=svc.id,
            partner_service_code="PAY-TGLU",
            partner_service_name="Glucose",
            price=200000,
            status=MAPPING_ACTIVE,
        )
        db.session.add(self.mapping)
        db.session.commit()
        SlotGenerationService.generate_partner_daily_slots(self.partner.id, days=2)
        self.demo = seed_payment_demo()
        self.invoice_id = self.demo["invoice_id"]
        self.payment_id = self.demo["payment_id"]

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_payment_gateway_apis(self):
        listing = self.client.get("/api/v1/payments")
        self.assertEqual(listing.status_code, 200)
        self.assertGreaterEqual(listing.get_json()["count"], 1)

        providers = self.client.get("/api/v1/payments/providers")
        self.assertEqual(providers.status_code, 200)
        self.assertIn(PAYMENT_PROVIDER_STRIPE, providers.get_json()["providers"])
        self.assertIn(PAYMENT_PROVIDER_VNPAY, providers.get_json()["providers"])
        self.assertIn(PAYMENT_PROVIDER_MOMO, providers.get_json()["providers"])

        for provider in [PAYMENT_PROVIDER_VNPAY, PAYMENT_PROVIDER_MOMO]:
            created = self.client.post(
                "/api/v1/payments/create",
                json={
                    "invoice_id": self.invoice_id,
                    "provider": provider,
                    "method_type": "EWALLET",
                },
            )
            self.assertEqual(created.status_code, 201)
            self.assertEqual(created.get_json()["payment"]["status"], PAYMENT_GATEWAY_COMPLETED)

        history = self.client.get("/api/v1/payments/history")
        self.assertEqual(history.status_code, 200)
        self.assertGreaterEqual(history.get_json()["count"], 1)

        transaction = PaymentTransaction.query.filter_by(payment_id=self.payment_id).first()
        webhook = self.client.post(
            "/api/v1/payments/webhook",
            json={
                "provider": PAYMENT_PROVIDER_STRIPE,
                "event_type": "payment.updated",
                "external_transaction_id": transaction.external_transaction_id,
                "status": PAYMENT_GATEWAY_COMPLETED,
            },
        )
        self.assertEqual(webhook.status_code, 200)
        self.assertGreaterEqual(PaymentWebhook.query.count(), 1)

        refund = self.client.post(
            "/api/v1/payments/refund",
            json={"payment_id": self.payment_id, "reason": "Demo refund"},
        )
        self.assertEqual(refund.status_code, 200)
        self.assertEqual(refund.get_json()["payment"]["status"], PAYMENT_GATEWAY_REFUNDED)

    def test_payment_gateway_web_routes(self):
        routes = {str(r) for r in self.app.url_map.iter_rules()}
        for route in ["/payment", "/payment/history", "/payment/refunds"]:
            self.assertIn(route, routes)


if __name__ == "__main__":
    unittest.main()
