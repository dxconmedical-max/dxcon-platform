import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REPORTING_SEED_ORDERS"] = "25"
os.environ["REPORTING_SEED_TESTS"] = "100"

from app import create_app
from app.core.statuses import (
    KPI_CODE_AI_INTERPRETATION,
    KPI_CODE_COLLECTOR_UTILIZATION,
    KPI_CODE_CRITICAL_RESULTS,
    KPI_CODE_DOCTOR_REVIEW_TIME,
    KPI_CODE_ORDERS,
    KPI_CODE_REVENUE,
    KPI_CODE_SAMPLES,
    KPI_CODE_SLA,
    KPI_CODE_TAT,
    KPI_CODE_TESTS,
    KPI_CODE_TRANSPORT_TIME,
)
from app.extensions.db import db
from app.services.kpi_engine_service import KPIEngineService
from scripts.seed_reporting_demo import seed_reporting_demo


REQUIRED_METRICS = [
    KPI_CODE_ORDERS,
    KPI_CODE_SAMPLES,
    KPI_CODE_TESTS,
    KPI_CODE_REVENUE,
    KPI_CODE_COLLECTOR_UTILIZATION,
    KPI_CODE_TRANSPORT_TIME,
    KPI_CODE_TAT,
    KPI_CODE_SLA,
    KPI_CODE_CRITICAL_RESULTS,
    KPI_CODE_AI_INTERPRETATION,
    KPI_CODE_DOCTOR_REVIEW_TIME,
]


def verify_kpi_calculations():
    with app.app_context():
        db.create_all()
        seed_reporting_demo()
        for period in ["DAILY", "WEEKLY", "MONTHLY", "QUARTERLY", "YEARLY"]:
            payload = KPIEngineService.compute_period(period, persist=True)
            missing = [code for code in REQUIRED_METRICS if code not in payload["metrics"]]
            if missing:
                print("MISSING KPI metrics for", period, missing)
                return False
            print("OK: KPI", period, "metrics", len(payload["metrics"]))
        listing = KPIEngineService.list_records(page=1, page_size=20)
        if listing["total"] < len(REQUIRED_METRICS):
            print("MISSING: persisted KPI records")
            return False
        print("OK: KPI records persisted", listing["total"])
        return True


app = create_app()
print("\n=== DXCON KPI VERIFY ===\n")
if not verify_kpi_calculations():
    print("\nKPI VERIFY FAILED\n")
    sys.exit(1)
print("\nKPI VERIFY PASSED\n")
