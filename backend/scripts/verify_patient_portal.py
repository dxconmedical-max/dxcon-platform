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
from app.models.patient import Patient
from app.services.patient_portal_service import PatientDashboardService
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_patient_portal_demo import seed_patient_portal_demo, seed_patient_portal_flow
from scripts.seed_scheduling_demo import seed_scheduling_demo


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/patient/dashboard",
        "/api/v1/patient/profile",
        "/api/v1/patient/results",
        "/api/v1/patient/orders",
        "/api/v1/patient/timeline",
        "/api/v1/patient/notifications",
        "/api/v1/patient/share-report",
        "/api/v1/patient/consent",
        "/patient",
        "/patient/profile",
        "/patient/results",
        "/patient/orders",
        "/patient/timeline",
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
            db.session.add(Company(company_code="DX-PP", company_name="DxCon", tax_code="01"))
            db.session.commit()
        seed_marketplace_demo()
        seed_scheduling_demo()
        demo = seed_patient_portal_demo()
        mapping = PartnerServiceMapping.query.first()
        flow = seed_patient_portal_flow(mapping)
        if flow.get("orders_created", 0) < 1:
            print("MISSING: patient portal demo flow")
            return False
        print("OK: patient portal demo seed")

        patient = Patient.query.get(demo["patient_id"])
        dashboard = PatientDashboardService.get_dashboard(patient.id)
        if dashboard["summary"]["orders_total"] < 1:
            print("MISSING: patient dashboard data")
            return False
        print("OK: patient portal dashboard")
        return True


app = create_app()
print("\n=== DXCON PATIENT PORTAL VERIFY ===\n")
errors = 0
if not verify_routes(app):
    errors += 1
if not verify_seed_and_flow():
    errors += 1
if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nPATIENT PORTAL VERIFY PASSED\n")
