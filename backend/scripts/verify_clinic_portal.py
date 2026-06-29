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
from app.services.clinic_portal_service import ClinicDashboardService
from scripts.seed_clinic_portal_demo import seed_clinic_portal_demo, seed_clinic_portal_flow
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_scheduling_demo import seed_scheduling_demo


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/clinic/dashboard",
        "/api/v1/clinic/profile",
        "/api/v1/clinic/bookings",
        "/api/v1/clinic/orders",
        "/api/v1/clinic/patients",
        "/api/v1/clinic/doctors",
        "/api/v1/clinic/revenue",
        "/clinic",
        "/clinic/dashboard",
        "/clinic/bookings",
        "/clinic/orders",
        "/clinic/patients",
        "/clinic/revenue",
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
            db.session.add(Company(company_code="DX-CLN", company_name="DxCon", tax_code="01"))
            db.session.commit()
        seed_marketplace_demo()
        seed_scheduling_demo()
        demo = seed_clinic_portal_demo()
        mapping = PartnerServiceMapping.query.first()
        flow = seed_clinic_portal_flow(mapping=mapping)
        if not flow.get("patient_id"):
            print("MISSING: clinic portal demo flow")
            return False
        print("OK: clinic portal demo seed")

        dashboard = ClinicDashboardService.get_dashboard(demo["clinic_id"])
        if dashboard["summary"]["patients_total"] < 1:
            print("MISSING: clinic dashboard data")
            return False
        print("OK: clinic portal dashboard")
        return True


app = create_app()
print("\n=== DXCON CLINIC PORTAL VERIFY ===\n")
errors = 0
if not verify_routes(app):
    errors += 1
if not verify_seed_and_flow():
    errors += 1
if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nCLINIC PORTAL VERIFY PASSED\n")
