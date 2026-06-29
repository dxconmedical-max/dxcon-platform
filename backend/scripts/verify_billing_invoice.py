import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import BILLING_INVOICE_PAID
from app.extensions.db import db
from app.models.billing_ledger import BillingLedger
from app.models.company import Company
from app.models.tax_record import TaxRecord
from app.services.billing_service import BillingService, InvoiceService
from scripts.seed_billing_demo import seed_billing_demo
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_scheduling_demo import seed_scheduling_demo


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/billing/invoices",
        "/api/v1/billing/ledger",
        "/api/v1/billing/summary",
        "/billing",
        "/billing/invoices",
        "/billing/ledger",
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
            db.session.add(Company(company_code="DX-BIL", company_name="DxCon", tax_code="01"))
            db.session.commit()
        seed_marketplace_demo()
        seed_scheduling_demo()
        summary = seed_billing_demo()
        if summary["invoices_created"] < 1:
            print("MISSING: billing demo invoices")
            return False
        print("OK: billing invoice demo seed")

        invoice = BillingService.list_invoices()[0]
        if invoice.billing_status != BILLING_INVOICE_PAID:
            print("MISSING: paid invoice in demo")
            return False

        payload = BillingService.get_summary()
        if payload["invoices_total"] < 1:
            print("MISSING: billing summary")
            return False
        print("OK: billing summary")

        if BillingLedger.query.count() < 1:
            print("MISSING: billing ledger entries")
            return False
        print("OK: billing ledger")

        if TaxRecord.query.count() < 1:
            print("MISSING: tax records")
            return False
        print("OK: tax records")
        return True


app = create_app()
print("\n=== DXCON BILLING INVOICE VERIFY ===\n")
errors = 0
if not verify_routes(app):
    errors += 1
if not verify_seed_and_flow():
    errors += 1
if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nBILLING INVOICE VERIFY PASSED\n")
