"""Idempotent demo dataset seeding for staging/production demos."""

from __future__ import annotations

import importlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import inspect as sa_inspect

from app.core.passwords import hash_password
from app.core.roles import ACCOUNTING, ADMIN, COLLECTOR, DOCTOR, LAB, SUPER_ADMIN
from app.extensions.db import db

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "DEMO_SEED_REPORT.json"

DEMO_DOMAIN = "demo.dxcon.test"
DEMO_PASSWORD = "DemoPass123!"
DEMO_COMPANY_CODE = "DEMO-CMP-001"

TARGETS = {
    "super_admin_users": 1,
    "admin_staff_users": 5,
    "doctor_users": 10,
    "laboratories": 5,
    "partners_clinics": 10,
    "patients": 100,
    "test_catalog_items": 200,
    "orders": 50,
    "order_items": 50,
    "sample_collections": 20,
    "collectors_drivers": 10,
    "shipments": 20,
    "invoices": 10,
    "notifications": 10,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def demo_email(kind: str, index: int) -> str:
    if kind == "superadmin":
        return f"demo-superadmin@{DEMO_DOMAIN}"
    return f"demo-{kind}-{index:02d}@{DEMO_DOMAIN}"


def demo_code(prefix: str, index: int) -> str:
    return f"DEMO-{prefix}-{index:03d}"


def import_model(module_path: str, class_name: str):
    try:
        module = importlib.import_module(module_path)
        return getattr(module, class_name), None
    except (ImportError, AttributeError):
        return None, "model_not_found"


def table_exists(model) -> bool:
    try:
        inspector = sa_inspect(db.engine)
        return model.__tablename__ in inspector.get_table_names()
    except Exception:
        return False


def count_demo_rows(model, field: str, prefix: str) -> int:
    column = getattr(model, field)
    return model.query.filter(column.like(f"{prefix}%")).count()


def ensure_user(email: str, role: str, *, dry_run: bool, phone: str | None = None):
    from app.models.user import User

    existing = User.query.filter_by(email=email).first()
    if existing:
        return existing, False
    if dry_run:
        return None, True
    user = User(
        email=email,
        phone=phone,
        role=role,
        password_hash=hash_password(DEMO_PASSWORD),
        is_active=True,
    )
    db.session.add(user)
    return user, True


def run_seed(*, dry_run: bool = False, summary_only: bool = False) -> dict:
    start = time.perf_counter()
    created_counts: dict[str, int] = {}
    existing_counts: dict[str, int] = {}
    skipped_models: list[dict[str, Any]] = []
    errors: list[str] = []

    def skip(name: str, reason: str):
        skipped_models.append({"model": name, "skipped": True, "reason": reason})

    def seed_domain(name: str, model_path: str, class_name: str, runner: Callable[[Any], None]):
        model, reason = import_model(model_path, class_name)
        if model is None:
            skip(name, reason or "model_not_found")
            return
        if not table_exists(model):
            skip(name, "table_not_found")
            return
        try:
            runner(model)
        except Exception as exc:
            errors.append(f"{name}: {exc}")

    def record(name: str, created: int, existing: int):
        created_counts[name] = created
        existing_counts[name] = existing

    if summary_only:
        summary_models = [
            ("users", "app.models.user", "User", "email", "demo-"),
            ("patients", "app.models.patient", "Patient", "patient_code", "DEMO-PAT-"),
            ("test_catalog", "app.models.test_catalog", "TestCatalog", "code", "DEMO-TST-"),
            ("orders", "app.models.order", "Order", "order_code", "DEMO-ORD-"),
        ]
        for name, module, cls, field, prefix in summary_models:
            model, reason = import_model(module, cls)
            if model is None or not table_exists(model):
                skip(name, reason or "table_not_found")
                existing_counts[name] = 0
                continue
            existing_counts[name] = count_demo_rows(model, field, prefix)
            created_counts[name] = 0
        report = _build_report("summary", created_counts, existing_counts, skipped_models, errors, start)
        write_report(report)
        return report

    # Users
    def seed_users(_model):
        created = existing = 0
        user, made = ensure_user(demo_email("superadmin", 1), SUPER_ADMIN, dry_run=dry_run, phone="0900000000")
        created += int(made)
        existing += int(not made and user is not None)
        roles = [ADMIN, ADMIN, ADMIN, ACCOUNTING, ACCOUNTING]
        for index, role in enumerate(roles, start=1):
            _, made = ensure_user(demo_email("admin", index), role, dry_run=dry_run, phone=f"090100{index:04d}")
            created += int(made)
            existing += int(not made)
        for index in range(1, TARGETS["doctor_users"] + 1):
            _, made = ensure_user(demo_email("doctor", index), DOCTOR, dry_run=dry_run, phone=f"090200{index:04d}")
            created += int(made)
            existing += int(not made)
        if not dry_run and created:
            db.session.commit()
        record("users", created, existing)

    seed_domain("users", "app.models.user", "User", seed_users)

    # Laboratories
    def seed_laboratories(model):
        prefix = "DEMO-LAB-"
        existing = count_demo_rows(model, "code", prefix)
        created = 0
        for index in range(1, TARGETS["laboratories"] + 1):
            code = demo_code("LAB", index)
            if model.query.filter_by(code=code).first():
                continue
            if dry_run:
                created += 1
                continue
            db.session.add(
                model(
                    code=code,
                    name=f"Demo Laboratory {index}",
                    address=f"{index} Demo Lab Street",
                    phone=f"0288{index:06d}",
                    email=demo_email("lab", index),
                    is_active=True,
                )
            )
            created += 1
        if not dry_run and created:
            db.session.commit()
        record("laboratories", created, existing)

    seed_domain("laboratories", "app.models.laboratory", "Laboratory", seed_laboratories)

    # Partners / clinics
    def seed_partners(model):
        prefix = "DEMO-CLN-"
        existing = count_demo_rows(model, "partner_code", prefix)
        created = 0
        for index in range(1, TARGETS["partners_clinics"] + 1):
            code = demo_code("CLN", index)
            if model.query.filter_by(partner_code=code).first():
                continue
            if dry_run:
                created += 1
                continue
            db.session.add(
                model(
                    partner_code=code,
                    partner_type="CLINIC",
                    legal_name=f"Demo Clinic {index} Co., Ltd",
                    display_name=f"Demo Clinic {index}",
                    email=demo_email("clinic", index),
                    phone=f"090300{index:04d}",
                    status="ACTIVE",
                )
            )
            created += 1
        if not dry_run and created:
            db.session.commit()
        record("partners_clinics", created, existing)

    seed_domain("partners_clinics", "app.models.partner", "Partner", seed_partners)

    # Doctor profiles
    def seed_doctor_profiles(model):
        prefix = "DEMO-DOC-"
        existing = count_demo_rows(model, "doctor_code", prefix)
        created = 0
        for index in range(1, TARGETS["doctor_users"] + 1):
            code = demo_code("DOC", index)
            if model.query.filter_by(doctor_code=code).first():
                continue
            if dry_run:
                created += 1
                continue
            doctor_id = f"demo-doctor-id-{index:03d}"
            db.session.add(
                model(
                    doctor_id=doctor_id,
                    doctor_code=code,
                    full_name=f"Dr. Demo {index}",
                    license_number=f"DEMO-LIC-{index:03d}",
                    email=demo_email("doctor", index),
                    phone=f"090200{index:04d}",
                    specialty_primary="General Practice",
                    status="ACTIVE",
                )
            )
            created += 1
        if not dry_run and created:
            db.session.commit()
        record("doctor_profiles", created, existing)

    seed_domain("doctor_profiles", "app.models.doctor_profile", "DoctorProfile", seed_doctor_profiles)

    # Demo company for billing
    def seed_company(model):
        existing = 1 if model.query.filter_by(company_code=DEMO_COMPANY_CODE).first() else 0
        created = 0
        if existing:
            record("companies", created, existing)
            return
        if dry_run:
            record("companies", 1, 0)
            return
        db.session.add(
            model(
                company_code=DEMO_COMPANY_CODE,
                company_name="Demo Corporate Billing",
                tax_code="DEMO-TAX-001",
                contact_person="Demo Billing Contact",
                phone="0909999000",
                email=f"demo-billing@{DEMO_DOMAIN}",
                status="ACTIVE",
            )
        )
        db.session.commit()
        record("companies", 1, 0)

    seed_domain("companies", "app.models.company", "Company", seed_company)

    # Test catalog
    def seed_test_catalog(model):
        prefix = "DEMO-TST-"
        existing = count_demo_rows(model, "code", prefix)
        created = 0
        for index in range(1, TARGETS["test_catalog_items"] + 1):
            code = demo_code("TST", index)
            if model.query.filter_by(code=code).first():
                continue
            if dry_run:
                created += 1
                continue
            db.session.add(
                model(
                    code=code,
                    name=f"Demo Test {index}",
                    category="General",
                    sample_type="Blood",
                    price=float(10 + (index % 50)),
                )
            )
            created += 1
        if not dry_run and created:
            db.session.commit()
        record("test_catalog_items", created, existing)

    seed_domain("test_catalog_items", "app.models.test_catalog", "TestCatalog", seed_test_catalog)

    # Patients
    def seed_patients(model):
        prefix = "DEMO-PAT-"
        existing = count_demo_rows(model, "patient_code", prefix)
        created = 0
        for index in range(1, TARGETS["patients"] + 1):
            code = demo_code("PAT", index)
            if model.query.filter_by(patient_code=code).first():
                continue
            if dry_run:
                created += 1
                continue
            db.session.add(
                model(
                    patient_code=code,
                    full_name=f"Demo Patient {index}",
                    gender="M" if index % 2 else "F",
                    date_of_birth=f"1990-{(index % 12) + 1:02d}-{(index % 28) + 1:02d}",
                    phone=f"091000{index:04d}",
                    email=f"demo-patient-{index:03d}@{DEMO_DOMAIN}",
                    address=f"{index} Demo Patient Street",
                )
            )
            created += 1
        if not dry_run and created:
            db.session.commit()
        record("patients", created, existing)

    seed_domain("patients", "app.models.patient", "Patient", seed_patients)

    # Orders and order items
    def seed_orders_and_items(order_model):
        from app.models.order_item import OrderItem
        from app.models.laboratory import Laboratory
        from app.models.patient import Patient
        from app.models.test_catalog import TestCatalog

        if not table_exists(OrderItem):
            skip("order_items", "table_not_found")
            return

        order_prefix = "DEMO-ORD-"
        existing_orders = count_demo_rows(order_model, "order_code", order_prefix)
        created_orders = created_items = 0
        patients = labs = tests = []
        if not dry_run:
            patients = Patient.query.filter(Patient.patient_code.like("DEMO-PAT-%")).order_by(Patient.patient_code).all()
            labs = Laboratory.query.filter(Laboratory.code.like("DEMO-LAB-%")).order_by(Laboratory.code).all()
            tests = TestCatalog.query.filter(TestCatalog.code.like("DEMO-TST-%")).order_by(TestCatalog.code).all()
        for index in range(1, TARGETS["orders"] + 1):
            code = demo_code("ORD", index)
            if order_model.query.filter_by(order_code=code).first():
                continue
            if dry_run:
                created_orders += 1
                created_items += 1
                continue
            if not patients or not tests:
                break
            patient = patients[(index - 1) % len(patients)]
            lab = labs[(index - 1) % len(labs)] if labs else None
            test = tests[(index - 1) % len(tests)]
            order = order_model(
                order_code=code,
                patient_id=patient.id,
                laboratory_id=lab.id if lab else None,
                status="PENDING",
                total_amount=float(test.price or 0),
            )
            db.session.add(order)
            db.session.flush()
            db.session.add(
                OrderItem(
                    order_id=order.id,
                    test_catalog_id=test.id,
                    price=float(test.price or 0),
                )
            )
            created_orders += 1
            created_items += 1
        if not dry_run and (created_orders or created_items):
            db.session.commit()
        existing_items = (
            OrderItem.query.join(order_model, OrderItem.order_id == order_model.id)
            .filter(order_model.order_code.like("DEMO-ORD-%"))
            .count()
        )
        record("orders", created_orders, existing_orders)
        record("order_items", created_items, existing_items)

    seed_domain("orders", "app.models.order", "Order", seed_orders_and_items)

    # Sample collections
    def seed_sample_collections(model):
        from app.models.order import Order

        existing = model.query.join(Order, model.order_id == Order.id).filter(Order.order_code.like("DEMO-ORD-%")).count()
        created = 0
        if dry_run:
            for index in range(1, TARGETS["sample_collections"] + 1):
                code = demo_code("ORD", index)
                order = Order.query.filter_by(order_code=code).first()
                if order and model.query.filter_by(order_id=order.id).first():
                    continue
                created += 1
            record("sample_collections", created, existing)
            return
        orders = Order.query.filter(Order.order_code.like("DEMO-ORD-%")).order_by(Order.order_code).limit(
            TARGETS["sample_collections"]
        ).all()
        for index, order in enumerate(orders, start=1):
            if model.query.filter_by(order_id=order.id).first():
                continue
            if dry_run:
                created += 1
                continue
            db.session.add(
                model(
                    order_id=order.id,
                    collector_name=f"Demo Collector {index}",
                    status="PENDING",
                )
            )
            created += 1
        if not dry_run and created:
            db.session.commit()
        record("sample_collections", created, existing)

    seed_domain("sample_collections", "app.models.sample_collection", "SampleCollection", seed_sample_collections)

    # Collectors / drivers
    def seed_collectors(model):
        prefix = "DEMO-COL-"
        existing = count_demo_rows(model, "driver_code", prefix)
        created = 0
        for index in range(1, TARGETS["collectors_drivers"] + 1):
            code = demo_code("COL", index)
            if model.query.filter_by(driver_code=code).first():
                continue
            if dry_run:
                created += 1
                continue
            db.session.add(
                model(
                    driver_code=code,
                    full_name=f"Demo Collector {index}",
                    phone=f"092000{index:04d}",
                    email=demo_email("collector", index),
                    vehicle_no=f"DEMO-{index:02d}",
                    status="ACTIVE",
                )
            )
            created += 1
        if not dry_run and created:
            db.session.commit()
        record("collectors_drivers", created, existing)

    seed_domain("collectors_drivers", "app.models.driver", "Driver", seed_collectors)

    # Shipments
    def seed_shipments(model):
        prefix = "DEMO-SHP-"
        existing = count_demo_rows(model, "shipment_code", prefix)
        created = 0
        for index in range(1, TARGETS["shipments"] + 1):
            code = demo_code("SHP", index)
            if model.query.filter_by(shipment_code=code).first():
                continue
            if dry_run:
                created += 1
                continue
            db.session.add(
                model(
                    shipment_code=code,
                    lab_name=f"Demo Laboratory {(index % 5) + 1}",
                    status="CREATED",
                    sample_count=1,
                )
            )
            created += 1
        if not dry_run and created:
            db.session.commit()
        record("shipments", created, existing)

    seed_domain("shipments", "app.models.shipment", "Shipment", seed_shipments)

    # Invoices
    def seed_invoices(model):
        from app.models.company import Company
        from app.models.order import Order

        prefix = "DEMO-INV-"
        existing = count_demo_rows(model, "invoice_no", prefix)
        created = 0
        if dry_run:
            for index in range(1, TARGETS["invoices"] + 1):
                invoice_no = demo_code("INV", index)
                if model.query.filter_by(invoice_no=invoice_no).first():
                    continue
                created += 1
            record("invoices", created, existing)
            return
        company = Company.query.filter_by(company_code=DEMO_COMPANY_CODE).first()
        orders = Order.query.filter(Order.order_code.like("DEMO-ORD-%")).order_by(Order.order_code).limit(TARGETS["invoices"]).all()
        if not company or not orders:
            record("invoices", 0, existing)
            return
        for index, order in enumerate(orders, start=1):
            invoice_no = demo_code("INV", index)
            if model.query.filter_by(invoice_no=invoice_no).first():
                continue
            if dry_run:
                created += 1
                continue
            db.session.add(
                model(
                    invoice_no=invoice_no,
                    company_id=company.id,
                    order_id=order.id,
                    total_amount=order.total_amount,
                    payment_status="UNPAID",
                    billing_status="DRAFT",
                )
            )
            created += 1
        if not dry_run and created:
            db.session.commit()
        record("invoices", created, existing)

    seed_domain("invoices", "app.models.invoice", "Invoice", seed_invoices)

    # Notifications
    def seed_notifications(model):
        prefix = "DEMO-NOT-"
        existing = count_demo_rows(model, "notification_code", prefix)
        created = 0
        for index in range(1, TARGETS["notifications"] + 1):
            code = demo_code("NOT", index)
            if model.query.filter_by(notification_code=code).first():
                continue
            if dry_run:
                created += 1
                continue
            db.session.add(
                model(
                    notification_code=code,
                    template_code="DEMO_TEMPLATE",
                    subject=f"Demo Notification {index}",
                    body=f"This is demo notification body {index}.",
                    status="PENDING",
                    priority="NORMAL",
                    reference_type="ORDER",
                )
            )
            created += 1
        if not dry_run and created:
            db.session.commit()
        record("notifications", created, existing)

    seed_domain("notifications", "app.models.notification", "Notification", seed_notifications)

    mode = "dry_run" if dry_run else "apply"
    report = _build_report(mode, created_counts, existing_counts, skipped_models, errors, start)
    write_report(report)
    return report


def _build_report(mode, created_counts, existing_counts, skipped_models, errors, start):
    return {
        "generated_at": utc_now(),
        "mode": mode,
        "targets": TARGETS,
        "created_counts": created_counts,
        "existing_counts": existing_counts,
        "skipped_models": skipped_models,
        "errors": errors,
        "runtime_seconds": round(time.perf_counter() - start, 3),
        "ok": not errors,
        "demo_accounts": demo_account_summary(),
    }


def demo_account_summary() -> dict:
    return {
        "super_admin": demo_email("superadmin", 1),
        "admin_staff_pattern": f"demo-admin-01@{DEMO_DOMAIN} .. demo-admin-05@{DEMO_DOMAIN}",
        "doctor_pattern": f"demo-doctor-01@{DEMO_DOMAIN} .. demo-doctor-10@{DEMO_DOMAIN}",
        "password": DEMO_PASSWORD,
        "code_prefixes": ["DEMO-LAB-", "DEMO-CLN-", "DEMO-PAT-", "DEMO-TST-", "DEMO-ORD-"],
    }


def write_report(report: dict) -> str:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return str(REPORT_PATH)
