import json
import os
import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.core.statuses import BILLING_INVOICE_PAID, PARTNER_ACTIVE
from app.extensions.db import db
from app.models.clinic_profile import ClinicProfile
from app.models.company import Company
from app.models.driver import Driver
from app.models.invoice import Invoice
from app.models.lab_result import LabResult
from app.models.lab_result_item import LabResultItem
from app.models.medical_order import MedicalOrder
from app.models.partner import Partner
from app.models.reporting_platform import (
    ClinicAnalytics,
    CollectorAnalytics,
    KPIRecord,
    LabAnalytics,
    MetricSnapshot,
    PartnerAnalytics,
    ReportDefinition,
    RevenueAnalytics,
)
from app.services.dashboard_platform_service import DashboardPlatformService
from app.services.kpi_engine_service import KPIEngineService
from app.services.report_platform_service import ReportPlatformService


TARGETS = {
    "orders": int(os.environ.get("REPORTING_SEED_ORDERS", "5000")),
    "tests": int(os.environ.get("REPORTING_SEED_TESTS", "20000")),
    "collectors": int(os.environ.get("REPORTING_SEED_COLLECTORS", "500")),
    "laboratories": int(os.environ.get("REPORTING_SEED_LABS", "50")),
    "clinics": int(os.environ.get("REPORTING_SEED_CLINICS", "100")),
    "partners": int(os.environ.get("REPORTING_SEED_PARTNERS", "200")),
    "snapshot_months": int(os.environ.get("REPORTING_SEED_MONTHS", "24")),
}


def _rand_dt(months_back=24):
    days = random.randint(0, months_back * 30)
    return datetime.utcnow() - timedelta(days=days)


def _ensure_company():
    if Company.query.first():
        return
    db.session.add(Company(company_code="DX-RPT", company_name="DxCon Analytics", tax_code="01"))
    db.session.commit()


def _seed_partners():
    existing = Partner.query.count()
    to_create = max(TARGETS["partners"] - existing, 0)
    labs_needed = max(TARGETS["laboratories"] - Partner.query.filter_by(partner_type="LABORATORY").count(), 0)
    for idx in range(to_create):
        is_lab = idx < labs_needed
        db.session.add(
            Partner(
                partner_code=f"PTR-RPT-{existing + idx + 1:04d}",
                partner_type="LABORATORY" if is_lab else random.choice(["CLINIC", "IMAGING", "HOME_CARE"]),
                legal_name=f"Partner {existing + idx + 1}",
                display_name=f"Partner {existing + idx + 1}",
                status=PARTNER_ACTIVE,
                pickup_sla_minutes=random.randint(30, 120),
            )
        )
    db.session.commit()
    return Partner.query.all()


def _seed_clinics():
    existing = ClinicProfile.query.count()
    to_create = max(TARGETS["clinics"] - existing, 0)
    for idx in range(to_create):
        cid = str(uuid.uuid4())
        db.session.add(
            ClinicProfile(
                clinic_id=cid,
                clinic_code=f"CLN-RPT-{existing + idx + 1:04d}",
                name=f"Clinic {existing + idx + 1}",
                status="ACTIVE",
            )
        )
    db.session.commit()


def _seed_collectors():
    existing = Driver.query.count()
    to_create = max(TARGETS["collectors"] - existing, 0)
    for idx in range(to_create):
        db.session.add(
            Driver(
                driver_code=f"COL-RPT-{existing + idx + 1:04d}",
                full_name=f"Collector {existing + idx + 1}",
                phone=f"090{existing + idx + 1:07d}",
                status="ACTIVE",
            )
        )
    db.session.commit()
    return Driver.query.all()


def _seed_orders_and_tests(partners, collectors):
    existing_orders = MedicalOrder.query.count()
    orders_to_create = max(TARGETS["orders"] - existing_orders, 0)
    existing_tests = LabResultItem.query.count()
    tests_to_create = max(TARGETS["tests"] - existing_tests, 0)

    partner_ids = [p.id for p in partners] or [None]
    collector_ids = [c.id for c in collectors] or [None]
    company = Company.query.first()

    created_orders = 0
    created_tests = 0
    order_seq = existing_orders

    while created_orders < orders_to_create or created_tests < tests_to_create:
        order_seq += 1
        order_id = str(uuid.uuid4())
        result_id = str(uuid.uuid4())
        created_at = _rand_dt(TARGETS["snapshot_months"])
        partner_id = random.choice(partner_ids)
        collector_id = random.choice(collector_ids)

        if created_orders < orders_to_create:
            db.session.add(
                MedicalOrder(
                    id=order_id,
                    order_code=f"MO-RPT-{order_seq:06d}",
                    patient_name=f"Patient {order_seq}",
                    patient_phone="0900000000",
                    partner_id=partner_id,
                    collector_id=collector_id,
                    status=random.choice(["BOOKED", "COLLECTED", "IN_LAB", "COMPLETED", "RESULT_READY"]),
                    total_amount=random.randint(100000, 500000),
                    created_at=created_at,
                    updated_at=created_at,
                )
            )
            created_orders += 1
            if company and random.random() < 0.6:
                db.session.add(
                    Invoice(
                        invoice_no=f"INV-RPT-{order_seq:06d}",
                        company_id=company.id,
                        order_id=order_id,
                        medical_order_id=order_id,
                        partner_id=partner_id,
                        total_amount=random.randint(100000, 500000),
                        billing_status=random.choice([BILLING_INVOICE_PAID, "DRAFT", "ISSUED"]),
                        created_at=created_at,
                    )
                )
            db.session.add(
                LabResult(
                    id=result_id,
                    result_code=f"LR-RPT-{order_seq:06d}",
                    medical_order_id=order_id,
                    partner_id=partner_id,
                    patient_name=f"Patient {order_seq}",
                    source_type="MANUAL",
                    status=random.choice(["VALIDATED", "IN_REVIEW", "APPROVED", "RELEASED"]),
                    created_at=created_at,
                )
            )

        tests_for_order = 0
        while created_tests < tests_to_create and tests_for_order < 5:
            db.session.add(
                LabResultItem(
                    lab_result_id=result_id,
                    test_code=f"T{tests_for_order + 1}",
                    test_name=random.choice(["Glucose", "TSH", "HbA1c", "CBC", "CRP"]),
                    result_value=str(round(random.uniform(1, 20), 1)),
                    unit="mmol/L",
                    reference_range="3.9-6.1",
                    flag=random.choice(["NORMAL", "HIGH", "LOW", "CRITICAL"]),
                    created_at=created_at,
                )
            )
            created_tests += 1
            tests_for_order += 1

        if order_seq % 250 == 0:
            db.session.commit()

    db.session.commit()
    return created_orders, created_tests


def _seed_monthly_snapshots():
    snapshots_created = 0
    anchor = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    for month_idx in range(TARGETS["snapshot_months"]):
        period_end = anchor - timedelta(days=month_idx * 30)
        period_start = period_end - timedelta(days=30)
        metrics = {
            "orders": random.randint(150, 450),
            "tests": random.randint(600, 1800),
            "revenue": random.randint(50000000, 150000000),
            "sla_compliance": round(random.uniform(85, 99), 2),
        }
        db.session.add(
            MetricSnapshot(
                snapshot_code=f"MS-SEED-{month_idx + 1:03d}",
                metric_domain="PLATFORM",
                period_type="MONTHLY",
                period_start=period_start,
                period_end=period_end,
                metrics_json=json.dumps(metrics),
            )
        )
        db.session.add(
            RevenueAnalytics(
                analytics_code=f"REV-SEED-{month_idx + 1:03d}",
                period_start=period_start,
                period_end=period_end,
                gross_revenue=metrics["revenue"],
                net_revenue=metrics["revenue"] * 0.92,
                invoice_count=random.randint(100, 400),
                metrics_json=json.dumps(metrics),
            )
        )
        db.session.add(
            LabAnalytics(
                analytics_code=f"LAB-SEED-{month_idx + 1:03d}",
                period_start=period_start,
                period_end=period_end,
                tests_total=metrics["tests"],
                tat_avg_hours=round(random.uniform(12, 36), 2),
                critical_rate=round(random.uniform(0.5, 4.5), 2),
                pending_reviews=random.randint(5, 40),
                metrics_json=json.dumps(metrics),
            )
        )
        db.session.add(
            PartnerAnalytics(
                analytics_code=f"PTR-SEED-{month_idx + 1:03d}",
                period_start=period_start,
                period_end=period_end,
                orders_total=metrics["orders"],
                revenue_total=metrics["revenue"],
                sla_compliance_rate=metrics["sla_compliance"],
                metrics_json=json.dumps(metrics),
            )
        )
        db.session.add(
            CollectorAnalytics(
                analytics_code=f"COL-SEED-{month_idx + 1:03d}",
                period_start=period_start,
                period_end=period_end,
                orders_assigned=random.randint(50, 200),
                orders_completed=random.randint(40, 190),
                utilization_rate=round(random.uniform(60, 95), 2),
                transport_time_avg_minutes=round(random.uniform(20, 55), 2),
                metrics_json=json.dumps(metrics),
            )
        )
        db.session.add(
            ClinicAnalytics(
                analytics_code=f"CLN-SEED-{month_idx + 1:03d}",
                period_start=period_start,
                period_end=period_end,
                orders_total=random.randint(20, 120),
                revenue_total=random.randint(5000000, 25000000),
                patient_count=random.randint(10, 80),
                metrics_json=json.dumps(metrics),
            )
        )
        db.session.add(
            KPIRecord(
                record_code=f"KPI-SEED-{month_idx + 1:03d}",
                period_type="MONTHLY",
                period_start=period_start,
                period_end=period_end,
                kpi_code="ORDERS",
                kpi_value=metrics["orders"],
                dimension="PLATFORM",
            )
        )
        snapshots_created += 1
    db.session.commit()
    return snapshots_created


def seed_reporting_demo():
    _ensure_company()
    partners = _seed_partners()
    _seed_clinics()
    collectors = _seed_collectors()
    orders_created, tests_created = _seed_orders_and_tests(partners, collectors)
    snapshots_created = _seed_monthly_snapshots()
    ReportPlatformService.ensure_definitions()
    DashboardPlatformService.ensure_default_widgets()
    KPIEngineService.compute_monthly(persist=True)

    return {
        "orders_created": MedicalOrder.query.count(),
        "tests_created": LabResultItem.query.count(),
        "collectors_created": Driver.query.count(),
        "laboratories_created": Partner.query.filter_by(partner_type="LABORATORY").count(),
        "clinics_created": ClinicProfile.query.count(),
        "partners_created": Partner.query.count(),
        "snapshots_created": MetricSnapshot.query.count(),
        "definitions_created": ReportDefinition.query.count(),
        "batch_orders_added": orders_created,
        "batch_tests_added": tests_created,
        "monthly_snapshots_added": snapshots_created,
    }


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        summary = seed_reporting_demo()
        print("\n=== DXCON REPORTING DEMO SEED ===\n")
        for key, value in summary.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
