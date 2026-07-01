import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.crm_activity import Activity
from app.models.crm_lead import CrmLead
from app.models.crm_organization import Customer, Organization
from app.models.crm_pipeline import Opportunity
from app.models.crm_quotation import Quotation
from app.models.crm_sales_contract import SalesContract
from app.services.crm_dashboard_service import CrmDashboardService
from app.services.crm_service import CrmService
from app.services.quotation_service import QuotationService
from app.services.sales_contract_service import SalesContractService
from scripts.seed_crm_demo import seed_crm_demo


def verify_models_import():
    models = [
        CrmLead,
        Customer,
        Organization,
        Opportunity,
        Activity,
        Quotation,
        SalesContract,
    ]
    for model in models:
        assert model.__tablename__
    print("OK: CRM models import")


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/crm/leads",
        "/api/v1/crm/customers",
        "/api/v1/crm/opportunities",
        "/api/v1/crm/activities",
        "/api/v1/crm/pipelines",
        "/api/v1/crm/quotations",
        "/api/v1/crm/contracts",
        "/api/v1/crm/dashboard",
    ]
    ok = True
    for route in required:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            ok = False
    return ok


def verify_seed_and_flow():
    summary = seed_crm_demo(force=True)
    checks = [
        ("leads", 100),
        ("customers", 50),
        ("organizations", 20),
        ("opportunities", 30),
        ("contracts", 15),
        ("quotations", 50),
    ]
    for key, minimum in checks:
        if summary.get(key, 0) < minimum:
            print(f"MISSING: {key} expected >= {minimum}, got {summary.get(key)}")
            return False
        print(f"OK: {key}={summary[key]}")
    if summary.get("activities", 0) < 50:
        print("MISSING: activities")
        return False
    print("OK: activities=", summary["activities"])
    return True


def verify_services():
    dashboard = CrmDashboardService.get_dashboard()
    required_keys = [
        "summary",
        "lead_funnel",
        "top_customers",
        "top_sales",
        "expiring_contracts",
    ]
    for key in required_keys:
        if key not in dashboard:
            print("MISSING: dashboard key", key)
            return False
    print("OK: dashboard payload")

    lead = CrmService.create_lead({"company_name": "Verify Lead"})
    advanced = CrmService.advance_lead_stage(lead.id)
    if advanced.pipeline_stage == "LEAD":
        print("MISSING: lead stage advance")
        return False
    print("OK: lead workflow")

    customer = Customer.query.first()
    quotation = QuotationService.generate_quotation({"customer_id": customer.id})
    if quotation.total_amount <= 0:
        print("MISSING: quotation generation")
        return False
    print("OK: quotation generation")

    expiring = SalesContractService.expiring_contracts(within_days=60)
    print("OK: expiring contracts count=", len(expiring))
    return True


def verify_api(client):
    response = client.get("/api/v1/crm/leads?page=1&per_page=5")
    if response.status_code != 200:
        print("MISSING: leads list API")
        return False
    print("OK: leads list API")

    response = client.get("/api/v1/crm/dashboard")
    if response.status_code != 200:
        print("MISSING: dashboard API")
        return False
    print("OK: dashboard API")
    return True


app = create_app()

with app.app_context():
    db.create_all()
    print("=== CRM Release 3.1 Verification ===")
    verify_models_import()
    routes_ok = verify_routes(app)
    seed_ok = verify_seed_and_flow()
    services_ok = verify_services()
    api_ok = verify_api(app.test_client())

    score = sum([routes_ok, seed_ok, services_ok, api_ok])
    print(f"\nVerification score: {score}/4")
    if score == 4:
        print("CRM Release 3.1: PASS")
    else:
        print("CRM Release 3.1: FAIL")
        sys.exit(1)
