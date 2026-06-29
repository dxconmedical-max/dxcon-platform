import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.company import Company
from app.models.payment_transaction import PaymentTransaction
from app.models.payment_webhook import PaymentWebhook
from app.services.payment_gateway_service import PaymentGatewayService, PaymentService
from scripts.seed_payment_demo import seed_payment_demo


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/payments",
        "/api/v1/payments/create",
        "/api/v1/payments/webhook",
        "/api/v1/payments/refund",
        "/api/v1/payments/history",
        "/payment",
        "/payment/history",
        "/payment/refunds",
    ]
    for route in required:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            return False
    return True


def verify_providers():
    providers = PaymentGatewayService.supported_providers()
    for code in ["STRIPE", "VNPAY", "MOMO"]:
        if code in providers:
            print("OK: provider", code)
        else:
            print("MISSING: provider", code)
            return False
    return True


def verify_seed_and_flow():
    with app.app_context():
        db.create_all()
        if not Company.query.first():
            db.session.add(Company(company_code="DX-PAY-V", company_name="DxCon", tax_code="01"))
            db.session.commit()
        demo = seed_payment_demo()
        if not demo.get("payment_id"):
            print("MISSING: payment demo flow")
            return False
        print("OK: payment demo seed")

        payments = PaymentService.list_payments()
        if payments["count"] < 1:
            print("MISSING: payment list")
            return False
        print("OK: payment list")

        history = PaymentService.get_history()
        if history["count"] < 1:
            print("MISSING: payment history")
            return False
        print("OK: payment history")

        if PaymentTransaction.query.count() < 1:
            print("MISSING: payment transactions")
            return False
        print("OK: payment transactions")
        return True


app = create_app()
print("\n=== DXCON PAYMENT GATEWAY VERIFY ===\n")
errors = 0
if not verify_routes(app):
    errors += 1
if not verify_providers():
    errors += 1
if not verify_seed_and_flow():
    errors += 1
if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nPAYMENT GATEWAY VERIFY PASSED\n")
