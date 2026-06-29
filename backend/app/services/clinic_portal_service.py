import json
import uuid
from datetime import datetime, timedelta

from app.core.audit import write_audit
from app.core.statuses import (
    CLINIC_BOOKING_CONFIRMED,
    CLINIC_BOOKING_PENDING,
    CLINIC_DOCTOR_ACTIVE,
    CLINIC_ORDER_COMPLETED,
    CLINIC_ORDER_PENDING,
    CLINIC_PATIENT_ACTIVE,
    CLINIC_PROFILE_ACTIVE,
)
from app.extensions.db import db
from app.models.clinic_booking import ClinicBooking
from app.models.clinic_department import ClinicDepartment
from app.models.clinic_doctor import ClinicDoctor
from app.models.clinic_order import ClinicOrder
from app.models.clinic_patient import ClinicPatient
from app.models.clinic_profile import ClinicProfile
from app.models.clinic_referral import ClinicReferral
from app.models.clinic_revenue_summary import ClinicRevenueSummary
from app.models.doctor_profile import DoctorProfile
from app.models.invoice import Invoice
from app.models.partner import Partner
from app.models.patient import Patient


class ClinicPortalError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ClinicPortalService:

    @staticmethod
    def _get_profile_or_raise(clinic_id):
        profile = ClinicProfile.query.filter_by(clinic_id=clinic_id).first()
        if not profile:
            raise ClinicPortalError("Clinic profile not found", 404)
        return profile

    @staticmethod
    def ensure_profile(clinic_id=None, data=None):
        data = data or {}
        profile = ClinicProfile.query.filter_by(clinic_id=clinic_id).first() if clinic_id else None
        if profile:
            return profile

        clinic_id = clinic_id or str(uuid.uuid4())
        profile = ClinicProfile(
            clinic_id=clinic_id,
            clinic_code=data.get("clinic_code") or f"CLN-{ClinicProfile.query.count() + 1:04d}",
            name=data.get("name") or "Clinic",
            legal_name=data.get("legal_name"),
            tax_code=data.get("tax_code"),
            email=data.get("email"),
            phone=data.get("phone"),
            address=data.get("address"),
            partner_id=data.get("partner_id"),
            settings_json=json.dumps(data.get("settings") or {}),
            status=CLINIC_PROFILE_ACTIVE,
        )
        db.session.add(profile)
        db.session.commit()
        return profile

    @staticmethod
    def get_profile(clinic_id):
        profile = ClinicPortalService._get_profile_or_raise(clinic_id)
        departments = ClinicDepartment.query.filter_by(clinic_id=clinic_id).all()
        doctors = ClinicDoctor.query.filter_by(clinic_id=clinic_id, status=CLINIC_DOCTOR_ACTIVE).all()
        partner = Partner.query.get(profile.partner_id) if profile.partner_id else None
        return {
            "profile": profile.to_dict(),
            "departments": [row.to_dict() for row in departments],
            "doctors": [row.to_dict() for row in doctors],
            "partner": partner.to_dict() if partner else None,
        }

    @staticmethod
    def update_profile(clinic_id, data, actor_email="SYSTEM", ip_address=""):
        profile = ClinicPortalService._get_profile_or_raise(clinic_id)

        for field in ["name", "legal_name", "tax_code", "email", "phone", "address", "status", "partner_id"]:
            if field in data:
                setattr(profile, field, data[field])
        if "settings" in data:
            profile.settings_json = json.dumps(data["settings"])

        for dept in data.get("departments", []):
            db.session.add(
                ClinicDepartment(
                    clinic_id=clinic_id,
                    department_code=dept.get("department_code"),
                    name=dept.get("name"),
                    status=dept.get("status", CLINIC_PROFILE_ACTIVE),
                )
            )

        write_audit("CLINIC_PROFILE_UPDATE", "ClinicProfile", profile.id, actor_email, ip_address)
        db.session.commit()
        return ClinicPortalService.get_profile(clinic_id)

    @staticmethod
    def register_patient(clinic_id, patient_id, note=None):
        ClinicPortalService._get_profile_or_raise(clinic_id)
        patient = Patient.query.get(patient_id)
        if not patient:
            raise ClinicPortalError("Patient not found", 404)

        row = ClinicPatient.query.filter_by(clinic_id=clinic_id, patient_id=patient_id).first()
        if not row:
            row = ClinicPatient(
                clinic_id=clinic_id,
                patient_id=patient_id,
                status=CLINIC_PATIENT_ACTIVE,
                note=note,
            )
            db.session.add(row)
        else:
            row.status = CLINIC_PATIENT_ACTIVE
            row.note = note or row.note
        db.session.commit()
        return row

    @staticmethod
    def link_doctor(clinic_id, doctor_id, department_id=None, role="STAFF"):
        ClinicPortalService._get_profile_or_raise(clinic_id)
        doctor = DoctorProfile.query.filter_by(doctor_id=doctor_id).first()
        if not doctor:
            raise ClinicPortalError("Doctor not found", 404)

        row = ClinicDoctor.query.filter_by(clinic_id=clinic_id, doctor_id=doctor_id).first()
        if not row:
            row = ClinicDoctor(
                clinic_id=clinic_id,
                doctor_id=doctor_id,
                department_id=department_id,
                role=role,
                status=CLINIC_DOCTOR_ACTIVE,
            )
            db.session.add(row)
        else:
            row.status = CLINIC_DOCTOR_ACTIVE
            row.department_id = department_id or row.department_id
            row.role = role or row.role
        db.session.commit()
        return row

    @staticmethod
    def list_doctors(clinic_id):
        ClinicPortalService._get_profile_or_raise(clinic_id)
        rows = ClinicDoctor.query.filter_by(clinic_id=clinic_id).all()
        payload = []
        for row in rows:
            item = row.to_dict()
            doctor = DoctorProfile.query.filter_by(doctor_id=row.doctor_id).first()
            item["doctor"] = doctor.to_dict() if doctor else None
            payload.append(item)
        return {"count": len(payload), "doctors": payload}

    @staticmethod
    def list_patients(clinic_id):
        ClinicPortalService._get_profile_or_raise(clinic_id)
        rows = (
            ClinicPatient.query.filter_by(clinic_id=clinic_id, status=CLINIC_PATIENT_ACTIVE)
            .order_by(ClinicPatient.registered_at.desc())
            .all()
        )
        return {"count": len(rows), "patients": [row.to_dict() for row in rows]}


class ClinicDashboardService:

    @staticmethod
    def get_dashboard(clinic_id):
        profile = ClinicPortalService._get_profile_or_raise(clinic_id)
        bookings = ClinicBooking.query.filter_by(clinic_id=clinic_id).all()
        orders = ClinicOrder.query.filter_by(clinic_id=clinic_id).all()
        patients = ClinicPatient.query.filter_by(clinic_id=clinic_id, status=CLINIC_PATIENT_ACTIVE).count()
        doctors = ClinicDoctor.query.filter_by(clinic_id=clinic_id, status=CLINIC_DOCTOR_ACTIVE).count()
        referrals = ClinicReferral.query.filter_by(clinic_id=clinic_id).count()
        revenue = ClinicRevenueService.get_revenue_summary(clinic_id, persist=False)

        return {
            "clinic": profile.to_dict(),
            "summary": {
                "patients_total": patients,
                "doctors_total": doctors,
                "bookings_total": len(bookings),
                "bookings_pending": len([b for b in bookings if b.status == CLINIC_BOOKING_PENDING]),
                "orders_total": len(orders),
                "orders_completed": len([o for o in orders if o.status == CLINIC_ORDER_COMPLETED]),
                "referrals_total": referrals,
                "revenue_total": revenue.get("summary", {}).get("gross_amount", 0),
            },
            "recent_bookings": [
                item.to_dict()
                for item in sorted(bookings, key=lambda row: row.scheduled_at or datetime.min, reverse=True)[:5]
            ],
            "recent_orders": [
                item.to_dict()
                for item in sorted(orders, key=lambda row: row.created_at or datetime.min, reverse=True)[:5]
            ],
        }


class ClinicBookingService:

    @staticmethod
    def _generate_code():
        return f"CBK-{ClinicBooking.query.count() + 1:06d}"

    @staticmethod
    def list_bookings(clinic_id, status=None):
        ClinicPortalService._get_profile_or_raise(clinic_id)
        query = ClinicBooking.query.filter_by(clinic_id=clinic_id)
        if status:
            query = query.filter(ClinicBooking.status == status)
        rows = query.order_by(ClinicBooking.scheduled_at.desc()).all()
        return {"count": len(rows), "bookings": [row.to_dict() for row in rows]}

    @staticmethod
    def create_booking(clinic_id, data, actor_email="SYSTEM", ip_address=""):
        ClinicPortalService._get_profile_or_raise(clinic_id)
        patient_id = data.get("patient_id")
        service_name = data.get("service_name")
        scheduled_at = data.get("scheduled_at")
        if not patient_id or not service_name or not scheduled_at:
            raise ClinicPortalError("patient_id, service_name, and scheduled_at are required", 400)

        if isinstance(scheduled_at, str):
            scheduled_at = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00").split("+")[0])

        ClinicPortalService.register_patient(clinic_id, patient_id)
        booking = ClinicBooking(
            booking_code=ClinicBookingService._generate_code(),
            clinic_id=clinic_id,
            patient_id=patient_id,
            doctor_id=data.get("doctor_id"),
            service_name=service_name,
            scheduled_at=scheduled_at,
            status=data.get("status", CLINIC_BOOKING_CONFIRMED),
            notes=data.get("notes"),
        )
        db.session.add(booking)
        write_audit("CLINIC_BOOKING", "ClinicBooking", booking.id, actor_email, ip_address)
        db.session.commit()
        return booking


class ClinicOrderService:

    @staticmethod
    def _generate_code():
        return f"CLN-ORD-{ClinicOrder.query.count() + 1:06d}"

    @staticmethod
    def list_orders(clinic_id, status=None):
        ClinicPortalService._get_profile_or_raise(clinic_id)
        query = ClinicOrder.query.filter_by(clinic_id=clinic_id)
        if status:
            query = query.filter(ClinicOrder.status == status)
        rows = query.order_by(ClinicOrder.created_at.desc()).all()
        return {"count": len(rows), "orders": [row.to_dict() for row in rows]}

    @staticmethod
    def create_order(clinic_id, data, actor_email="SYSTEM", ip_address=""):
        ClinicPortalService._get_profile_or_raise(clinic_id)
        patient_id = data.get("patient_id")
        if not patient_id:
            raise ClinicPortalError("patient_id is required", 400)

        ClinicPortalService.register_patient(clinic_id, patient_id)
        order = ClinicOrder(
            order_code=ClinicOrderService._generate_code(),
            clinic_id=clinic_id,
            patient_id=patient_id,
            medical_order_id=data.get("medical_order_id"),
            total_amount=data.get("total_amount", 0),
            status=data.get("status", CLINIC_ORDER_PENDING),
        )
        db.session.add(order)
        write_audit("CLINIC_ORDER", "ClinicOrder", order.id, actor_email, ip_address)
        db.session.commit()
        return order


class ClinicRevenueService:

    @staticmethod
    def get_revenue_summary(clinic_id, period_days=30, persist=True):
        profile = ClinicPortalService._get_profile_or_raise(clinic_id)
        end = datetime.utcnow()
        start = end - timedelta(days=period_days)

        orders = ClinicOrder.query.filter(
            ClinicOrder.clinic_id == clinic_id,
            ClinicOrder.created_at >= start,
            ClinicOrder.created_at <= end,
        ).all()
        gross = sum(row.total_amount or 0 for row in orders)
        completed = [row for row in orders if row.status == CLINIC_ORDER_COMPLETED]
        net = sum(row.total_amount or 0 for row in completed)

        invoices = []
        if profile.partner_id:
            invoices = Invoice.query.filter(
                Invoice.partner_id == profile.partner_id,
                Invoice.created_at >= start,
                Invoice.created_at <= end,
            ).all()
            gross += sum(inv.total_amount or 0 for inv in invoices if inv.billing_status == "PAID")

        summary = ClinicRevenueSummary(
            clinic_id=clinic_id,
            period_start=start,
            period_end=end,
            gross_amount=gross,
            net_amount=net,
            orders_count=len(orders),
        )
        if persist:
            db.session.add(summary)
            db.session.commit()

        return {
            "summary": summary.to_dict(),
            "orders": [row.to_dict() for row in orders],
            "invoices": [row.to_dict() for row in invoices],
        }
