from flask import Blueprint
from datetime import datetime, timedelta
import uuid

from app.extensions.db import db

from app.models.patient import Patient
from app.models.company import Company
from app.models.contract import Contract
from app.models.laboratory import Laboratory
from app.models.test_catalog import TestCatalog
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.test_result import TestResult
from app.models.home_collection import HomeCollection
from app.models.sample_tracking import SampleTracking
from app.models.sample_event import SampleEvent
from app.models.driver import Driver
from app.models.transport_box import TransportBox
from app.models.dispatch_job import DispatchJob
from app.models.invoice import Invoice
from app.models.payment import Payment


seeds_bp = Blueprint("seeds", __name__, url_prefix="/api/v1/seeds")


def sid():
    return str(uuid.uuid4())[:8].upper()


@seeds_bp.route("/demo-operations", methods=["POST"])
def demo_operations():

    now = datetime.utcnow()
    batch = sid()

    lab = Laboratory(
        code=f"LAB-{batch}",
        name="DxCon Central Laboratory",
        address="Can Tho",
        phone="0292999000",
        email="lab@dxcon.vn",
        is_active=True
    )
    db.session.add(lab)

    company = Company(
        company_code=f"COMP-{batch}",
        company_name="DxCon Demo Clinic",
        tax_code=f"TAX-{batch}",
        contact_person="Demo Manager",
        phone="0909999999",
        email="clinic@dxcon.vn",
        address="Can Tho",
        status="ACTIVE"
    )
    db.session.add(company)
    db.session.commit()

    contract = Contract(
        contract_code=f"CTR-{batch}",
        company_id=company.id,
        title="DxCon Demo Contract",
        contract_type="LAB_SERVICE",
        start_date="2026-06-01",
        end_date="2027-06-01",
        status="ACTIVE",
        total_value=100000000
    )
    db.session.add(contract)

    tests = [
        TestCatalog(code=f"HBA1C-{batch}", name="HbA1c", category="Biochemistry", sample_type="Blood", price=250000),
        TestCatalog(code=f"CBC-{batch}", name="Complete Blood Count", category="Hematology", sample_type="Blood", price=150000),
        TestCatalog(code=f"GLU-{batch}", name="Glucose", category="Biochemistry", sample_type="Blood", price=120000),
        TestCatalog(code=f"LIPID-{batch}", name="Lipid Profile", category="Biochemistry", sample_type="Blood", price=300000),
    ]

    for test in tests:
        db.session.add(test)

    drivers = []
    for i in range(1, 6):
        driver = Driver(
            driver_code=f"DRV-{batch}-{i}",
            full_name=f"Demo Driver {i}",
            phone=f"09880000{i}",
            vehicle_no=f"65A-{1000+i}",
            status="ACTIVE" if i < 5 else "OFFLINE"
        )
        drivers.append(driver)
        db.session.add(driver)

    db.session.commit()

    boxes = []
    temps = [4.2, 5.1, 9.5]
    for i in range(1, 4):
        box = TransportBox(
            box_code=f"BOX-{batch}-{i}",
            driver_id=drivers[i - 1].id,
            temperature=temps[i - 1],
            battery_level=90 - i * 10,
            latitude="10.0452",
            longitude="105.7469",
            status="ONLINE"
        )
        box.update_alert_status()
        boxes.append(box)
        db.session.add(box)

    patients = []
    for i in range(1, 21):
        patient = Patient(
            patient_code=f"PT-{batch}-{i:03d}",
            full_name=f"Demo Patient {i}",
            gender="MALE" if i % 2 == 0 else "FEMALE",
            phone=f"0910000{i:03d}",
            email=f"patient{i}@demo.vn",
            address=f"Demo Address {i}, Can Tho"
        )
        patients.append(patient)
        db.session.add(patient)

    db.session.commit()

    orders = []
    results_count = 0

    for i, patient in enumerate(patients, start=1):
        order = Order(
            order_code=f"ORD-{batch}-{i:03d}",
            patient_id=patient.id,
            laboratory_id=lab.id,
            company_id=company.id,
            contract_id=contract.id,
            status="COMPLETED" if i % 2 == 0 else "PROCESSING",
            total_amount=0,
            created_at=now - timedelta(hours=i)
        )
        db.session.add(order)
        db.session.commit()

        total = 0
        selected_tests = tests[:2] if i % 2 == 0 else tests[1:]

        for test in selected_tests:
            item = OrderItem(
                order_id=order.id,
                test_catalog_id=test.id,
                price=test.price
            )
            db.session.add(item)
            db.session.commit()

            total += test.price or 0

            if test.name == "HbA1c":
                value = "6.8" if i % 3 == 0 else "5.4"
                flag = "HIGH" if i % 3 == 0 else "NORMAL"
                reference = "4.0-5.6"
                unit = "%"
                interpretation = "HbA1c cao hon nguong tham chieu." if flag == "HIGH" else "HbA1c trong nguong tham chieu."
            elif test.name == "Glucose":
                value = "145" if i % 4 == 0 else "92"
                flag = "HIGH" if i % 4 == 0 else "NORMAL"
                reference = "70-99"
                unit = "mg/dL"
                interpretation = "Glucose tang, can theo doi duong huyet." if flag == "HIGH" else "Glucose binh thuong."
            elif test.name == "Lipid Profile":
                value = "220" if i % 5 == 0 else "170"
                flag = "HIGH" if i % 5 == 0 else "NORMAL"
                reference = "<200"
                unit = "mg/dL"
                interpretation = "Lipid profile bat thuong." if flag == "HIGH" else "Lipid profile trong gioi han."
            else:
                value = "8.2"
                flag = "NORMAL"
                reference = "4.0-10.0"
                unit = "10^9/L"
                interpretation = "CBC can duoc dien giai theo tung chi so thanh phan."

            approved = i % 2 == 0

            result = TestResult(
                order_item_id=item.id,
                test_name=test.name,
                result_value=value,
                unit=unit,
                reference_range=reference,
                flag=flag,
                interpretation=interpretation,
                approval_status="APPROVED" if approved else "PENDING",
                approved_by="Dr. DxCon Medical Director" if approved else None,
                approved_at=(now - timedelta(hours=i)).strftime("%Y-%m-%d %H:%M:%S") if approved else None,
                doctor_license="VN-MED-000001" if approved else None,
                signature_id=f"SIG-{sid()}" if approved else None,
                created_at=now - timedelta(hours=i + 1)
            )
            db.session.add(result)
            results_count += 1

        order.total_amount = total
        orders.append(order)

    db.session.commit()

    samples = []
    event_types = ["CHECKED_IN", "IN_TRANSIT", "RECEIVED", "PROCESSING", "RESULT_CREATED", "DOCTOR_APPROVED"]

    for i, patient in enumerate(patients, start=1):
        collector_id = f"COLLECTOR-{((i - 1) % 5) + 1}"

        home = HomeCollection(
            patient_id=patient.id,
            collector_id=collector_id,
            address=f"Home Address {i}, Can Tho",
            scheduled_time=(now + timedelta(hours=i)).strftime("%Y-%m-%d %H:%M"),
            status="COMPLETED" if i % 3 != 0 else "REQUESTED",
            created_at=now - timedelta(hours=i + 6)
        )
        db.session.add(home)
        db.session.commit()

        sample = SampleTracking(
            sample_code=f"SMP-{batch}-{i:03d}",
            home_collection_id=home.id,
            collector_id=collector_id,
            transport_box_id=boxes[(i - 1) % len(boxes)].id,
            latitude="10.0452",
            longitude="105.7469",
            status=["CHECKED_IN", "IN_TRANSIT", "RECEIVED", "COMPLETED"][i % 4],
            created_at=now - timedelta(hours=i + 5),
            updated_at=now - timedelta(hours=i)
        )
        samples.append(sample)
        db.session.add(sample)
        db.session.commit()

        for j, event_type in enumerate(event_types):
            if j <= i % len(event_types):
                event = SampleEvent(
                    sample_tracking_id=sample.id,
                    event_type=event_type,
                    note=f"{event_type} for {sample.sample_code}",
                    created_at=now - timedelta(hours=i + 5 - j)
                )
                db.session.add(event)

    db.session.commit()

    for i, order in enumerate(orders[:10], start=1):
        invoice = Invoice(
            invoice_no=f"INV-{batch}-{i:03d}",
            company_id=company.id,
            order_id=order.id,
            total_amount=order.total_amount,
            payment_status="PAID" if i % 2 == 0 else "UNPAID",
            created_at=now - timedelta(days=i)
        )
        db.session.add(invoice)
        db.session.commit()

        if invoice.payment_status == "PAID":
            payment = Payment(
                invoice_id=invoice.id,
                amount=invoice.total_amount,
                payment_method="BANK_TRANSFER",
                payment_date=now - timedelta(days=i - 1),
                status="PAID"
            )
            db.session.add(payment)

    db.session.commit()

    for i in range(1, 11):
        job = DispatchJob(
            job_code=f"DSP-{batch}-{i:03d}",
            driver_id=drivers[(i - 1) % len(drivers)].id,
            transport_box_id=boxes[(i - 1) % len(boxes)].id,
            status="COMPLETED" if i % 3 != 0 else "PLANNED",
            start_latitude="10.0452",
            start_longitude="105.7469",
            destination_latitude="10.0340",
            destination_longitude="105.7800",
            total_distance_km=round(8 + i * 1.25, 2),
            estimated_minutes=25 + i * 4,
            created_at=now - timedelta(hours=i)
        )
        db.session.add(job)

    db.session.commit()

    return {
        "message": "Demo Operations Dataset V1 created",
        "batch": batch,
        "patients": len(patients),
        "orders": len(orders),
        "results": results_count,
        "samples": len(samples),
        "drivers": len(drivers),
        "transport_boxes": len(boxes),
        "dispatch_jobs": 10
    }
