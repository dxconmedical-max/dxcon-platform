import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import LAB_WF_PATIENT_PORTAL, LAB_WORKFLOW_STAGES
from app.extensions.db import db
from app.models.lab_accession import LabWorkflowTransition, SampleAccession
from app.models.lab_facility import Analyzer
from app.models.lab_operations import CriticalResult, QualityControl, TechnicianReview
from app.services.accession_service import AccessionService
from app.services.lab_dashboard_service import LabDashboardService
from scripts.seed_lab_operations_demo import seed_lab_operations_demo


def verify_models_import():
    models = [SampleAccession, Analyzer, QualityControl, CriticalResult, TechnicianReview]
    for model in models:
        assert model.__tablename__
    print("OK: lab operations models import")


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/lab/accessions",
        "/api/v1/lab/worklists",
        "/api/v1/lab/analyzers",
        "/api/v1/lab/queues",
        "/api/v1/lab/qc",
        "/api/v1/lab/reviews",
        "/api/v1/lab/releases",
        "/api/v1/lab/dashboard",
    ]
    ok = True
    for route in required:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            ok = False
    return ok


def verify_seed():
    summary = seed_lab_operations_demo(force=True)
    checks = [
        ("samples", 200),
        ("analyzers", 10),
        ("qc_records", 50),
        ("critical_results", 20),
        ("reviews", 30),
    ]
    for key, minimum in checks:
        if summary.get(key, 0) < minimum:
            print(f"MISSING: {key} expected >= {minimum}, got {summary.get(key)}")
            return False
        print(f"OK: {key}={summary[key]}")
    return True


def verify_workflow_transitions():
    accession = AccessionService.create_accession(
        {"sample_code": "VERIFY-SMP-001", "patient_name": "Verify Patient"}
    )
    for _ in range(len(LAB_WORKFLOW_STAGES) - 1):
        AccessionService.advance_accession(accession.id, actor="verify")
        accession = SampleAccession.query.get(accession.id)

    if accession.workflow_stage != LAB_WF_PATIENT_PORTAL:
        print("MISSING: full workflow did not reach PATIENT_PORTAL")
        return False

    transitions = LabWorkflowTransition.query.filter_by(accession_id=accession.id).count()
    if transitions < len(LAB_WORKFLOW_STAGES):
        print("MISSING: transition count", transitions)
        return False
    print("OK: workflow transitions=", transitions)

    dashboard = LabDashboardService.get_dashboard()
    required = [
        "pending_samples",
        "samples_in_analyzer",
        "qc_failed",
        "awaiting_review",
        "critical_results",
        "released_today",
        "average_tat_minutes",
        "sla_percent",
        "technician_productivity",
        "analyzer_utilization",
    ]
    for key in required:
        if key not in dashboard:
            print("MISSING: dashboard key", key)
            return False
    print("OK: dashboard metrics")
    return True


def verify_api(client):
    response = client.get("/api/v1/lab/accessions?page=1&per_page=5")
    if response.status_code != 200:
        print("MISSING: accessions list API")
        return False
    print("OK: accessions list API")

    response = client.get("/api/v1/lab/dashboard")
    if response.status_code != 200:
        print("MISSING: dashboard API")
        return False
    print("OK: dashboard API")
    return True


app = create_app()

with app.app_context():
    db.create_all()
    print("=== Lab Operations Release 3.2 Verification ===")
    verify_models_import()
    routes_ok = verify_routes(app)
    seed_ok = verify_seed()
    workflow_ok = verify_workflow_transitions()
    api_ok = verify_api(app.test_client())

    score = sum([routes_ok, seed_ok, workflow_ok, api_ok])
    print(f"\nVerification score: {score}/4")
    if score == 4:
        print("Lab Operations Release 3.2: PASS")
    else:
        print("Lab Operations Release 3.2: FAIL")
        sys.exit(1)
