import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import BILLING_INVOICE_PAID
from app.extensions.db import db
from app.models.commission_ledger import CommissionLedger
from app.models.company import Company
from app.models.partner_settlement import PartnerSettlement
from app.services.billing_service import BillingService
from app.services.commission_service import CommissionService
from app.services.order_workflow_service import OrderWorkflowService
from app.services.settlement_service import SettlementService
from scripts.seed_billing_demo import seed_billing_demo
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_scheduling_demo import seed_scheduling_demo


def verify_models_import():
    models = [Company, PartnerSettlement, CommissionLedger]
    for model in models:
        assert model.__tablename__
    print("OK: billing models import")


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/billing/invoices",
        "/api/v1/billing/payments",
        "/api/v1/billing/refunds",
        "/api/v1/billing/settlements",
        "/api/v1/billing/commissions",
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
        seed_marketplace_demo()
        seed_scheduling_demo()
        summary = seed_billing_demo()
        if summary["invoices_created"] < 1:
            print("MISSING: billing demo invoices")
            return False
        print("OK: billing demo seed")

        invoice = BillingService.list_invoices()[0]
        if invoice.billing_status != BILLING_INVOICE_PAID:
            print("MISSING: paid invoice status")
            return False
        print("OK: invoice and payment flow")

        if CommissionLedger.query.count() < 1:
            print("MISSING: commission ledger entries")
            return False
        print("OK: commission calculation")

        if PartnerSettlement.query.count() < 1:
            print("MISSING: partner settlement")
            return False
        print("OK: settlement flow")
        return True


app = create_app()

print("\n=== DXCON BILLING VERIFY ===\n")

errors = 0
try:
    verify_models_import()
except Exception as exc:
    print("MISSING: billing models import", exc)
    errors += 1

if not verify_routes(app):
    errors += 1

if not verify_seed_and_flow():
    errors += 1

if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)

print("\nBILLING VERIFY PASSED\n")
