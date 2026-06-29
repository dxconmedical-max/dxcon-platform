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
from app.services.doctor_portal_service import DoctorDashboardService
from scripts.seed_doctor_portal_demo import seed_doctor_portal_demo, seed_doctor_portal_flow
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_scheduling_demo import seed_scheduling_demo


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/doctor/dashboard",
        "/api/v1/doctor/profile",
        "/api/v1/doctor/patients",
        "/api/v1/doctor/results",
        "/api/v1/doctor/referrals",
        "/api/v1/doctor/followups",
        "/api/v1/doctor/schedule",
        "/doctor",
        "/doctor/dashboard",
        "/doctor/patients",
        "/doctor/results",
        "/doctor/referrals",
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
            db.session.add(Company(company_code="DX-DOC", company_name="DxCon", tax_code="01"))
            db.session.commit()
        seed_marketplace_demo()
        seed_scheduling_demo()
        demo = seed_doctor_portal_demo()
        mapping = PartnerServiceMapping.query.first()
        flow = seed_doctor_portal_flow(mapping=mapping)
        if not flow.get("patient_id"):
            print("MISSING: doctor portal demo flow")
            return False
        print("OK: doctor portal demo seed")

        dashboard = DoctorDashboardService.get_dashboard(demo["doctor_id"])
        if dashboard["summary"]["patients_total"] < 1:
            print("MISSING: doctor dashboard data")
            return False
        print("OK: doctor portal dashboard")
        return True


app = create_app()
print("\n=== DXCON DOCTOR PORTAL VERIFY ===\n")
errors = 0
if not verify_routes(app):
    errors += 1
if not verify_seed_and_flow():
    errors += 1
if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nDOCTOR PORTAL VERIFY PASSED\n")
