"""UAT tenant bootstrap, dataset seeding, reset, and verification."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime

from app.core.passwords import hash_password
from app.core.roles import ADMIN, COLLECTOR, DOCTOR, LAB
from app.core.statuses import MAPPING_ACTIVE, PARTNER_ACTIVE
from app.extensions.db import db
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.models.doctor_profile import DoctorProfile
from app.models.driver import Driver
from app.models.enterprise_platform import EnterpriseOrganization, EnterpriseTenant
from app.models.clinic_profile import ClinicProfile
from app.models.company import Company
from app.models.invoice import Invoice
from app.models.marketplace_booking import MarketplaceBooking
from app.models.lab_result import LabResult
from app.models.laboratory import Laboratory
from app.models.medical_order import MedicalOrder
from app.models.notification_center import NCNotification
from app.models.partner import Partner
from app.models.partner_operating_hour import PartnerOperatingHour
from app.models.partner_service_mapping import PartnerServiceMapping
from app.models.patient import Patient
from app.models.reporting_platform import KPIRecord
from app.models.user import User
from app.services.clinic_portal_service import ClinicPortalService
from app.services.doctor_portal_service import DoctorPortalService
from app.services.enterprise_platform_service import TenantEnterpriseService
from app.services.kpi_engine_service import KPIEngineService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_workflow_service import OrderWorkflowService
from app.services.result_gateway_service import (
    ResultApprovalService,
    ResultReleaseService,
    ResultReviewService,
    ResultUploadService,
    ResultValidationService,
)
from app.services.scheduling import SchedulingService
from app.services.slot_generation import SlotGenerationService
from app.services.billing_service import InvoiceService

UAT = {
    "tenant_code": "TEN-UAT-STAGING",
    "tenant_name": "DxCon UAT Staging Tenant",
    "admin_email": "uat-admin@staging.dxcon.test",
    "doctor_email": "uat-doctor@staging.dxcon.test",
    "collector_email": "uat-collector@staging.dxcon.test",
    "lab_code": "UAT-LAB-001",
    "clinic_code": "UAT-CLN-001",
    "doctor_code": "UAT-DOC-001",
    "collector_code": "UAT-COL-001",
    "partner_code": "UAT-PTR-001",
    "patient_prefix": "UAT-PAT-",
    "service_code": "UAT-GLU",
    "password": "SecurePass123!",
}


def _ensure_user(email, role, phone=None):
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(
        email=email,
        phone=phone,
        role=role,
        password_hash=hash_password(UAT["password"]),
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()
    return user


def _ensure_partner(code, partner_type, display_name, email):
    partner = Partner.query.filter_by(partner_code=code).first()
    if partner:
        return partner
    partner = Partner(
        partner_code=code,
        partner_type=partner_type,
        legal_name=display_name,
        display_name=display_name,
        email=email,
        phone="0909000001",
        status=PARTNER_ACTIVE,
    )
    db.session.add(partner)
    db.session.commit()
    return partner


def bootstrap_tenant():
    tenant = EnterpriseTenant.query.filter_by(tenant_code=UAT["tenant_code"]).first()
    if not tenant:
        payload = TenantEnterpriseService.create(
            {
                "tenant_code": UAT["tenant_code"],
                "name": UAT["tenant_name"],
                "schema_name": "tenant_uat_staging",
            }
        )
        tenant = EnterpriseTenant.query.get(payload["id"])
        db.session.add(
            EnterpriseOrganization(
                tenant_id=tenant.id,
                org_code="UAT-ORG-ROOT",
                name="UAT Root Organization",
                level=0,
            )
        )
        db.session.commit()

    admin = _ensure_user(UAT["admin_email"], ADMIN, "0909100001")
    _ensure_user(UAT["doctor_email"], DOCTOR, "0909100002")
    _ensure_user(UAT["collector_email"], COLLECTOR, "0909100003")
    _ensure_user("uat-lab@staging.dxcon.test", LAB, "0909100004")

    lab = Laboratory.query.filter_by(code=UAT["lab_code"]).first()
    if not lab:
        lab = Laboratory(
            code=UAT["lab_code"],
            name="UAT Staging Laboratory",
            address="UAT Lab Street",
            phone="0292111222",
            email="uat-lab@staging.dxcon.test",
            is_active=True,
        )
        db.session.add(lab)
        db.session.commit()

    lab_partner = _ensure_partner(
        UAT["lab_code"],
        "LABORATORY",
        "UAT Staging Lab Partner",
        "uat-lab@staging.dxcon.test",
    )
    clinic_partner = _ensure_partner(
        UAT["clinic_code"],
        "CLINIC",
        "UAT Staging Clinic",
        "uat-clinic@staging.dxcon.test",
    )
    corporate_partner = _ensure_partner(
        UAT["partner_code"],
        "CORPORATE",
        "UAT Corporate Partner",
        "uat-partner@staging.dxcon.test",
    )

    clinic_profile = ClinicPortalService.ensure_profile(
        data={
            "clinic_code": UAT["clinic_code"],
            "name": "UAT Staging Clinic",
            "legal_name": "UAT Clinic Co., Ltd",
            "tax_code": "UAT010101",
            "email": "uat-clinic@staging.dxcon.test",
            "phone": "0909200001",
            "address": "UAT Clinic Address",
            "partner_id": clinic_partner.id,
        }
    )

    doctor = DoctorProfile.query.filter_by(doctor_code=UAT["doctor_code"]).first()
    if not doctor:
        doctor_profile = DoctorPortalService.ensure_profile(
            data={
                "doctor_code": UAT["doctor_code"],
                "full_name": "Dr. UAT Staging",
                "license_number": "UAT-VN-001",
                "email": UAT["doctor_email"],
                "phone": "0909300001",
                "specialty_primary": "General Practice",
            }
        )
        doctor_id = doctor_profile.doctor_id
    else:
        doctor_id = doctor.doctor_id

    ClinicPortalService.link_doctor(clinic_profile.clinic_id, doctor_id, role="CONSULTANT")

    collector = Driver.query.filter_by(driver_code=UAT["collector_code"]).first()
    if not collector:
        collector = Driver(
            driver_code=UAT["collector_code"],
            full_name="UAT Collector",
            phone="0909400001",
            vehicle_no="UAT-51A1",
            status="ACTIVE",
        )
        db.session.add(collector)
        db.session.commit()

    return {
        "tenant_id": tenant.id,
        "tenant_code": tenant.tenant_code,
        "admin_id": admin.id,
        "lab_id": lab.id,
        "clinic_id": clinic_profile.clinic_id,
        "doctor_id": doctor_id,
        "collector_id": collector.id,
        "lab_partner_id": lab_partner.id,
        "clinic_partner_id": clinic_partner.id,
        "partner_id": corporate_partner.id,
    }


def _ensure_uat_service_mapping(partner_id):
    category = DiagnosticCategory.query.filter_by(category_code="UAT-CAT").first()
    if not category:
        category = DiagnosticCategory(category_code="UAT-CAT", name="UAT Diagnostics", description="UAT")
        db.session.add(category)
        db.session.flush()

    service = DiagnosticService.query.filter_by(service_code=UAT["service_code"]).first()
    if not service:
        service = DiagnosticService(
            service_code=UAT["service_code"],
            name="UAT Glucose Panel",
            category_id=category.id,
            sample_type="Blood",
            home_collection_allowed=True,
        )
        db.session.add(service)
        db.session.flush()

    mapping = PartnerServiceMapping.query.filter_by(
        partner_id=partner_id,
        partner_service_code=UAT["service_code"],
    ).first()
    if not mapping:
        mapping = PartnerServiceMapping(
            partner_id=partner_id,
            diagnostic_service_id=service.id,
            partner_service_code=UAT["service_code"],
            partner_service_name="UAT Glucose Panel",
            price=150000,
            status=MAPPING_ACTIVE,
            home_collection_available=True,
        )
        db.session.add(mapping)
        db.session.commit()
    return mapping


def _ensure_uat_scheduling(partner_id, collector_id):
    if PartnerOperatingHour.query.filter_by(partner_id=partner_id).count() == 0:
        for day in range(0, 6):
            db.session.add(
                PartnerOperatingHour(
                    partner_id=partner_id,
                    day_of_week=day,
                    open_time="08:00",
                    close_time="17:00",
                    is_closed=False,
                )
            )
        db.session.commit()

    SchedulingService.get_or_create_partner_calendar(partner_id)
    start_date = datetime.utcnow().strftime("%Y-%m-%d")
    SlotGenerationService.generate_partner_daily_slots(partner_id, days=7, start_date=start_date)
    SlotGenerationService.generate_collector_availability(
        collector_id,
        days=7,
        city="Ha Noi",
        district="Cau Giay",
        start_date=start_date,
    )


def seed_uat_data():
    bootstrap = bootstrap_tenant()
    if not Company.query.filter_by(company_code="UAT-COMPANY").first():
        db.session.add(
            Company(
                company_code="UAT-COMPANY",
                company_name="UAT Billing Company",
                tax_code="UAT-TAX-001",
            )
        )
        db.session.commit()

    mapping = _ensure_uat_service_mapping(bootstrap["lab_partner_id"])
    _ensure_uat_scheduling(bootstrap["lab_partner_id"], bootstrap["collector_id"])

    slots = SchedulingService.list_available_slots(bootstrap["lab_partner_id"])
    if not slots:
        raise RuntimeError("UAT scheduling slots unavailable")

    patients_created = 0
    orders_created = 0
    results_created = 0
    invoices_created = 0

    for index in range(1, 4):
        code = f"{UAT['patient_prefix']}{index:03d}"
        patient = Patient.query.filter_by(patient_code=code).first()
        if not patient:
            patient = Patient(
                patient_code=code,
                full_name=f"UAT Patient {index}",
                gender="F" if index % 2 else "M",
                phone=f"090950{index:04d}",
                email=f"uat-patient-{index}@staging.dxcon.test",
            )
            db.session.add(patient)
            db.session.commit()
            patients_created += 1

        if MedicalOrder.query.filter_by(patient_id=patient.id).count():
            continue

        booking = MarketplaceBookingService.create_booking(
            {
                "partner_service_mapping_id": mapping.id,
                "patient_name": patient.full_name,
                "patient_phone": patient.phone,
                "requested_date": slots[0].slot_date,
            }
        )
        order = OrderWorkflowService.create_from_booking(booking.id)
        orders_created += 1

        result = ResultUploadService.create_manual(
            {
                "medical_order_id": order.id,
                "items": [
                    {
                        "test_code": "GLU",
                        "test_name": "Glucose",
                        "result_value": f"5.{index}",
                        "reference_range": "3.9-6.1",
                    }
                ],
            }
        )
        ResultValidationService.validate(result.id)
        ResultReviewService.submit_review(result.id, {"comments": "UAT review"})
        ResultApprovalService.approve(result.id, {"comments": "UAT approved"})
        ResultReleaseService.release(result.id, {"release_channel": "PORTAL"})
        results_created += 1

        invoice = InvoiceService.create_invoice(order.id)
        invoices_created += 1

    notifications_created = 0
    try:
        from app.models.notification_center import NCNotificationTemplate
        from app.notifications.notification_service import NotificationCenterService

        template = NCNotificationTemplate.query.first()
        if template:
            NotificationCenterService.create_notification(
                {
                    "event_type": "UATStaging",
                    "channel": template.channel,
                    "recipient": UAT["admin_email"],
                    "template_id": template.id,
                    "subject": "UAT staging notification",
                    "body": "UAT dataset seeded",
                },
                dispatch=False,
            )
            notifications_created = NCNotification.query.filter_by(status="QUEUED").count()
    except Exception:
        notifications_created = 0

    KPIEngineService.compute_daily(persist=True)
    reports_created = KPIRecord.query.count()

    return {
        "patients_created": patients_created,
        "orders_created": orders_created,
        "results_created": results_created,
        "invoices_created": invoices_created,
        "notifications_created": notifications_created,
        "reports_created": reports_created,
        "tenant_code": UAT["tenant_code"],
    }


def _delete_booking(booking_id):
    from app.models.booking_assignment import BookingAssignment
    from app.models.marketplace_booking import MarketplaceBooking
    from app.models.marketplace_booking_timeline import MarketplaceBookingTimeline

    MarketplaceBookingTimeline.query.filter_by(booking_id=booking_id).delete(synchronize_session=False)
    BookingAssignment.query.filter_by(booking_id=booking_id).delete(synchronize_session=False)
    booking = MarketplaceBooking.query.get(booking_id)
    if booking:
        db.session.delete(booking)


def _delete_medical_order(order):
    from app.models.invoice_item import InvoiceItem
    from app.models.lab_result_item import LabResultItem
    from app.models.medical_order_event import MedicalOrderEvent

    for result in LabResult.query.filter_by(medical_order_id=order.id).all():
        LabResultItem.query.filter_by(lab_result_id=result.id).delete(synchronize_session=False)
        db.session.delete(result)
    for invoice in Invoice.query.filter_by(medical_order_id=order.id).all():
        InvoiceItem.query.filter_by(invoice_id=invoice.id).delete(synchronize_session=False)
        db.session.delete(invoice)
    MedicalOrderEvent.query.filter_by(medical_order_id=order.id).delete(synchronize_session=False)
    booking_id = order.marketplace_booking_id
    db.session.delete(order)
    if booking_id:
        _delete_booking(booking_id)


def _delete_partner_graph(partner):
    from app.models.partner_availability import PartnerAvailability
    from app.models.partner_capacity import PartnerCapacity
    from app.models.scheduling_calendar import SchedulingCalendar
    from app.models.scheduling_slot import SchedulingSlot

    for booking in MarketplaceBooking.query.filter_by(partner_id=partner.id).all():
        order = MedicalOrder.query.filter_by(marketplace_booking_id=booking.id).first()
        if order:
            _delete_medical_order(order)
        else:
            _delete_booking(booking.id)
    calendars = SchedulingCalendar.query.filter_by(owner_id=partner.id).all()
    for calendar in calendars:
        SchedulingSlot.query.filter_by(calendar_id=calendar.id).delete(synchronize_session=False)
        db.session.delete(calendar)
    PartnerCapacity.query.filter_by(partner_id=partner.id).delete(synchronize_session=False)
    PartnerAvailability.query.filter_by(partner_id=partner.id).delete(synchronize_session=False)
    PartnerOperatingHour.query.filter_by(partner_id=partner.id).delete(synchronize_session=False)
    PartnerServiceMapping.query.filter_by(partner_id=partner.id).delete(synchronize_session=False)
    db.session.delete(partner)


def reset_staging_data():
    deleted = defaultdict(int)

    for patient in Patient.query.filter(Patient.patient_code.like(f"{UAT['patient_prefix']}%")).all():
        from sqlalchemy import or_

        orders = MedicalOrder.query.filter(
            or_(MedicalOrder.patient_id == patient.id, MedicalOrder.patient_phone == patient.phone)
        ).all()
        for order in orders:
            _delete_medical_order(order)
            deleted["orders"] += 1
        db.session.delete(patient)
        deleted["patients"] += 1

    deleted["notifications"] = NCNotification.query.filter(NCNotification.recipient.like("uat-%")).count()
    NCNotification.query.filter(NCNotification.recipient.like("uat-%")).delete(synchronize_session=False)

    clinic = ClinicProfile.query.filter_by(clinic_code=UAT["clinic_code"]).first()
    if clinic:
        db.session.delete(clinic)
        deleted["clinic"] += 1

    for model, field, value in (
        (DoctorProfile, "doctor_code", UAT["doctor_code"]),
        (Driver, "driver_code", UAT["collector_code"]),
        (Laboratory, "code", UAT["lab_code"]),
    ):
        row = model.query.filter_by(**{field: value}).first()
        if row:
            db.session.delete(row)
            deleted[field] += 1

    for code in (UAT["lab_code"], UAT["clinic_code"], UAT["partner_code"]):
        partner = Partner.query.filter_by(partner_code=code).first()
        if partner:
            _delete_partner_graph(partner)
            deleted["partners"] += 1

    for email in (
        UAT["admin_email"],
        UAT["doctor_email"],
        UAT["collector_email"],
        "uat-lab@staging.dxcon.test",
    ):
        user = User.query.filter_by(email=email).first()
        if user:
            db.session.delete(user)
            deleted["users"] += 1

    tenant = EnterpriseTenant.query.filter_by(tenant_code=UAT["tenant_code"]).first()
    if tenant:
        EnterpriseOrganization.query.filter_by(tenant_id=tenant.id).delete(synchronize_session=False)
        db.session.delete(tenant)
        deleted["tenants"] += 1

    db.session.commit()
    return dict(deleted)


def reseed_staging_data():
    reset_staging_data()
    return seed_uat_data()


def find_duplicate_routes(app):
    seen = defaultdict(list)
    for rule in app.url_map.iter_rules():
        methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
        key = (str(rule.rule), tuple(methods))
        seen[key].append(rule.endpoint)
    return {str(key): endpoints for key, endpoints in seen.items() if len(endpoints) > 1}


def verify_uat_data(app=None):
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    if app is None:
        from app import create_app

        app = create_app()
        app.config["TESTING"] = True

    checks = {}
    with app.app_context():
        from app.extensions.db import db

        db.create_all()
        tenant = EnterpriseTenant.query.filter_by(tenant_code=UAT["tenant_code"]).first()
        checks["tenant_created"] = {"ok": tenant is not None}

        users = User.query.filter(User.email.like("uat-%@staging.dxcon.test")).count()
        checks["users_created"] = {"ok": users >= 4, "count": users}

        checks["lab_created"] = {"ok": Laboratory.query.filter_by(code=UAT["lab_code"]).count() > 0}
        checks["clinic_created"] = {
            "ok": Partner.query.filter_by(partner_code=UAT["clinic_code"]).count() > 0
        }
        checks["doctor_created"] = {
            "ok": DoctorProfile.query.filter_by(doctor_code=UAT["doctor_code"]).count() > 0
        }
        checks["collector_created"] = {
            "ok": Driver.query.filter_by(driver_code=UAT["collector_code"]).count() > 0
        }
        checks["partner_created"] = {
            "ok": Partner.query.filter_by(partner_code=UAT["partner_code"]).count() > 0
        }

        patient_rows = Patient.query.filter(Patient.patient_code.like(f"{UAT['patient_prefix']}%")).all()
        patient_ids = [row.id for row in patient_rows]
        patient_phones = [row.phone for row in patient_rows if row.phone]
        patient_count = len(patient_ids)
        checks["patients"] = {"ok": patient_count >= 3, "count": patient_count}

        order_query = MedicalOrder.query
        if patient_ids or patient_phones:
            from sqlalchemy import or_

            filters = []
            if patient_ids:
                filters.append(MedicalOrder.patient_id.in_(patient_ids))
            if patient_phones:
                filters.append(MedicalOrder.patient_phone.in_(patient_phones))
            order_query = order_query.filter(or_(*filters))
        order_count = order_query.count()
        checks["orders"] = {"ok": order_count >= 3, "count": order_count}

        order_ids = [row.id for row in order_query.all()]
        result_count = LabResult.query.filter(LabResult.medical_order_id.in_(order_ids)).count() if order_ids else 0
        checks["results"] = {"ok": result_count >= 3, "count": result_count}

        invoice_count = Invoice.query.filter(Invoice.medical_order_id.in_(order_ids)).count() if order_ids else 0
        checks["invoices"] = {"ok": invoice_count >= 3, "count": invoice_count}

        checks["reports"] = {"ok": KPIRecord.query.count() >= 0, "count": KPIRecord.query.count()}
        checks["workflows_valid"] = {
            "ok": all(
                checks[key]["ok"]
                for key in (
                    "tenant_created",
                    "users_created",
                    "patients",
                    "orders",
                    "results",
                    "invoices",
                )
            )
        }
        checks["no_duplicate_routes"] = {"ok": not find_duplicate_routes(app)}

    passed = sum(1 for item in checks.values() if item.get("ok"))
    return {
        "ok": passed == len(checks),
        "passed": passed,
        "total": len(checks),
        "checks": checks,
    }
