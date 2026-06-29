import json
import uuid
from datetime import datetime

from app.core.audit import write_audit
from app.core.statuses import (
    DOCTOR_FOLLOWUP_PENDING,
    DOCTOR_PATIENT_ACTIVE,
    DOCTOR_PROFILE_ACTIVE,
    DOCTOR_REFERRAL_PENDING,
    DOCTOR_REFERRAL_SENT,
    LAB_RESULT_RELEASED,
)
from app.extensions.db import db
from app.models.doctor_availability import DoctorAvailability
from app.models.doctor_follow_up import DoctorFollowUp
from app.models.doctor_note import DoctorNote
from app.models.doctor_patient import DoctorPatient
from app.models.doctor_profile import DoctorProfile
from app.models.doctor_referral import DoctorReferral
from app.models.doctor_dashboard import DoctorDashboard
from app.models.doctor_specialty import DoctorSpecialty
from app.models.lab_result import LabResult
from app.models.medical_order import MedicalOrder
from app.models.partner import Partner
from app.models.patient import Patient
from app.models.result_release import ResultRelease
from app.models.test_result import TestResult
from app.models.order import Order
from app.models.order_item import OrderItem


class DoctorPortalError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class DoctorPortalService:

    @staticmethod
    def _get_profile_or_raise(doctor_id):
        profile = DoctorProfile.query.filter_by(doctor_id=doctor_id).first()
        if not profile:
            raise DoctorPortalError("Doctor profile not found", 404)
        return profile

    @staticmethod
    def ensure_profile(doctor_id=None, data=None):
        data = data or {}
        profile = DoctorProfile.query.filter_by(doctor_id=doctor_id).first() if doctor_id else None
        if profile:
            return profile

        doctor_id = doctor_id or str(uuid.uuid4())
        profile = DoctorProfile(
            doctor_id=doctor_id,
            doctor_code=data.get("doctor_code") or f"DOC-{DoctorProfile.query.count() + 1:04d}",
            full_name=data.get("full_name") or "Doctor",
            license_number=data.get("license_number"),
            email=data.get("email"),
            phone=data.get("phone"),
            specialty_primary=data.get("specialty_primary"),
            favorite_services_json=json.dumps(data.get("favorite_services") or []),
            linked_clinics_json=json.dumps(data.get("linked_clinics") or []),
            bio=data.get("bio"),
            status=DOCTOR_PROFILE_ACTIVE,
        )
        db.session.add(profile)
        db.session.commit()
        return profile

    @staticmethod
    def _assigned_patients(doctor_id):
        return (
            DoctorPatient.query.filter_by(
                doctor_id=doctor_id,
                relationship_status=DOCTOR_PATIENT_ACTIVE,
            )
            .order_by(DoctorPatient.assigned_at.desc())
            .all()
        )

    @staticmethod
    def assign_patient(doctor_id, patient_id, note=None):
        DoctorPortalService._get_profile_or_raise(doctor_id)
        patient = Patient.query.get(patient_id)
        if not patient:
            raise DoctorPortalError("Patient not found", 404)

        row = DoctorPatient.query.filter_by(doctor_id=doctor_id, patient_id=patient_id).first()
        if not row:
            row = DoctorPatient(
                doctor_id=doctor_id,
                patient_id=patient_id,
                relationship_status=DOCTOR_PATIENT_ACTIVE,
                note=note,
            )
            db.session.add(row)
        else:
            row.relationship_status = DOCTOR_PATIENT_ACTIVE
            row.note = note or row.note
        db.session.commit()
        return row

    @staticmethod
    def get_profile(doctor_id):
        profile = DoctorPortalService._get_profile_or_raise(doctor_id)
        specialties = DoctorSpecialty.query.filter_by(doctor_id=doctor_id).all()
        availability = DoctorAvailability.query.filter_by(doctor_id=doctor_id).all()
        linked_clinics = json.loads(profile.linked_clinics_json or "[]")
        favorite_services = json.loads(profile.favorite_services_json or "[]")

        clinic_rows = []
        for clinic in linked_clinics:
            partner = Partner.query.get(clinic.get("partner_id")) if clinic.get("partner_id") else None
            clinic_rows.append(
                {
                    **clinic,
                    "partner": partner.to_dict() if partner else None,
                }
            )

        return {
            "profile": profile.to_dict(),
            "specialties": [row.to_dict() for row in specialties],
            "availability": [row.to_dict() for row in availability],
            "favorite_services": favorite_services,
            "linked_clinics": clinic_rows,
        }

    @staticmethod
    def update_profile(doctor_id, data, actor_email="SYSTEM", ip_address=""):
        profile = DoctorPortalService._get_profile_or_raise(doctor_id)

        for field in ["full_name", "license_number", "email", "phone", "specialty_primary", "bio", "status"]:
            if field in data:
                setattr(profile, field, data[field])
        if "favorite_services" in data:
            profile.favorite_services_json = json.dumps(data["favorite_services"])
        if "linked_clinics" in data:
            profile.linked_clinics_json = json.dumps(data["linked_clinics"])

        for specialty in data.get("specialties", []):
            row = DoctorSpecialty(
                doctor_id=doctor_id,
                specialty_code=specialty.get("specialty_code"),
                specialty_name=specialty.get("specialty_name"),
                is_primary=specialty.get("is_primary", False),
            )
            db.session.add(row)

        for slot in data.get("availability", []):
            row = DoctorAvailability(
                doctor_id=doctor_id,
                day_of_week=slot.get("day_of_week"),
                start_time=slot.get("start_time"),
                end_time=slot.get("end_time"),
                location=slot.get("location"),
                is_active=slot.get("is_active", True),
            )
            db.session.add(row)

        write_audit("DOCTOR_PROFILE_UPDATE", "DoctorProfile", profile.id, actor_email, ip_address)
        db.session.commit()
        return DoctorPortalService.get_profile(doctor_id)


class DoctorPatientService:

    @staticmethod
    def list_patients(doctor_id):
        DoctorPortalService._get_profile_or_raise(doctor_id)
        rows = DoctorPortalService._assigned_patients(doctor_id)
        return {"count": len(rows), "patients": [row.to_dict() for row in rows]}


class DoctorDashboardService:

    @staticmethod
    def get_dashboard(doctor_id):
        profile = DoctorPortalService._get_profile_or_raise(doctor_id)
        patients = DoctorPortalService._assigned_patients(doctor_id)
        referrals = DoctorReferral.query.filter_by(doctor_id=doctor_id).all()
        follow_ups = DoctorFollowUp.query.filter_by(doctor_id=doctor_id).all()
        notes = DoctorNote.query.filter_by(doctor_id=doctor_id).count()
        availability = DoctorAvailability.query.filter_by(doctor_id=doctor_id, is_active=True).all()

        patient_ids = [row.patient_id for row in patients]
        results_count = 0
        if patient_ids:
            orders = MedicalOrder.query.filter(MedicalOrder.patient_id.in_(patient_ids)).all()
            if orders:
                order_ids = [order.id for order in orders]
                results_count = LabResult.query.filter(
                    LabResult.medical_order_id.in_(order_ids),
                    LabResult.status == LAB_RESULT_RELEASED,
                ).count()

        summary = {
            "patients_total": len(patients),
            "referrals_total": len(referrals),
            "follow_ups_pending": len(
                [item for item in follow_ups if item.status == DOCTOR_FOLLOWUP_PENDING]
            ),
            "notes_total": notes,
            "released_results_total": results_count,
            "schedule_slots": len(availability),
        }

        payload = {
            "doctor": profile.to_dict(),
            "summary": summary,
            "schedule_summary": [slot.to_dict() for slot in availability],
            "recent_referrals": [
                item.to_dict()
                for item in sorted(referrals, key=lambda row: row.created_at or datetime.min, reverse=True)[:5]
            ],
        }

        snapshot = DoctorDashboard(
            doctor_id=doctor_id,
            patients_total=summary["patients_total"],
            referrals_total=summary["referrals_total"],
            follow_ups_pending=summary["follow_ups_pending"],
            notes_total=summary["notes_total"],
            released_results_total=summary["released_results_total"],
            schedule_slots=summary["schedule_slots"],
            snapshot_json=json.dumps(summary),
        )
        db.session.add(snapshot)
        db.session.commit()
        payload["dashboard_snapshot"] = snapshot.to_dict()
        return payload

    @staticmethod
    def get_schedule(doctor_id):
        DoctorPortalService._get_profile_or_raise(doctor_id)
        availability = DoctorAvailability.query.filter_by(doctor_id=doctor_id, is_active=True).all()
        follow_ups = (
            DoctorFollowUp.query.filter_by(doctor_id=doctor_id)
            .order_by(DoctorFollowUp.follow_up_date.asc())
            .all()
        )
        return {
            "availability": [row.to_dict() for row in availability],
            "follow_ups": [row.to_dict() for row in follow_ups],
        }

    @staticmethod
    def list_results(doctor_id):
        DoctorPortalService._get_profile_or_raise(doctor_id)
        rows = DoctorPortalService._assigned_patients(doctor_id)
        patient_ids = [row.patient_id for row in rows]
        results_payload = []

        if patient_ids:
            medical_orders = MedicalOrder.query.filter(MedicalOrder.patient_id.in_(patient_ids)).all()
            for order in medical_orders:
                lab_results = LabResult.query.filter_by(medical_order_id=order.id).all()
                for result in lab_results:
                    item = result.to_dict(include_items=True)
                    item["patient_id"] = order.patient_id
                    item["order_code"] = order.order_code
                    item["review_ready"] = result.status == LAB_RESULT_RELEASED
                    release = (
                        ResultRelease.query.filter_by(lab_result_id=result.id)
                        .order_by(ResultRelease.released_at.desc())
                        .first()
                    )
                    item["release"] = release.to_dict() if release else None
                    notes = DoctorNote.query.filter_by(
                        doctor_id=doctor_id,
                        lab_result_id=result.id,
                    ).all()
                    item["doctor_notes"] = [note.to_dict() for note in notes]
                    results_payload.append(item)

        for patient_id in patient_ids:
            legacy_orders = Order.query.filter_by(patient_id=patient_id).all()
            for order in legacy_orders:
                items = OrderItem.query.filter_by(order_id=order.id).all()
                for order_item in items:
                    test_result = TestResult.query.filter_by(order_item_id=order_item.id).first()
                    if test_result:
                        results_payload.append(
                            {
                                "source": "LEGACY",
                                "patient_id": patient_id,
                                "order_code": order.order_code,
                                "result": test_result.to_dict(),
                            }
                        )

        return {"count": len(results_payload), "results": results_payload}


class DoctorReferralService:

    @staticmethod
    def _generate_code():
        return f"REF-{DoctorReferral.query.count() + 1:06d}"

    @staticmethod
    def create_referral(doctor_id, data, actor_email="SYSTEM", ip_address=""):
        DoctorPortalService._get_profile_or_raise(doctor_id)
        patient_id = data.get("patient_id")
        test_name = data.get("test_name")
        if not patient_id or not test_name:
            raise DoctorPortalError("patient_id and test_name are required", 400)

        DoctorPortalService.assign_patient(doctor_id, patient_id)
        referral = DoctorReferral(
            referral_code=DoctorReferralService._generate_code(),
            doctor_id=doctor_id,
            patient_id=patient_id,
            partner_id=data.get("partner_id"),
            test_code=data.get("test_code"),
            test_name=test_name,
            status=DOCTOR_REFERRAL_SENT,
            notes=data.get("notes"),
        )
        db.session.add(referral)
        write_audit("DOCTOR_REFERRAL", "DoctorReferral", referral.id, actor_email, ip_address)
        db.session.commit()
        return referral

    @staticmethod
    def list_referrals(doctor_id, status=None):
        DoctorPortalService._get_profile_or_raise(doctor_id)
        query = DoctorReferral.query.filter_by(doctor_id=doctor_id)
        if status:
            query = query.filter(DoctorReferral.status == status)
        rows = query.order_by(DoctorReferral.created_at.desc()).all()
        return {"count": len(rows), "referrals": [row.to_dict() for row in rows]}


class DoctorFollowUpService:

    @staticmethod
    def _generate_code():
        return f"FUP-{DoctorFollowUp.query.count() + 1:06d}"

    @staticmethod
    def create_follow_up(doctor_id, data, actor_email="SYSTEM", ip_address=""):
        DoctorPortalService._get_profile_or_raise(doctor_id)
        patient_id = data.get("patient_id")
        follow_up_date = data.get("follow_up_date")
        if not patient_id or not follow_up_date:
            raise DoctorPortalError("patient_id and follow_up_date are required", 400)

        if isinstance(follow_up_date, str):
            follow_up_date = datetime.fromisoformat(follow_up_date.replace("Z", "+00:00").split("+")[0])

        DoctorPortalService.assign_patient(doctor_id, patient_id)
        follow_up = DoctorFollowUp(
            follow_up_code=DoctorFollowUpService._generate_code(),
            doctor_id=doctor_id,
            patient_id=patient_id,
            follow_up_date=follow_up_date,
            status=DOCTOR_FOLLOWUP_PENDING,
            reminder_sent=data.get("reminder_sent", False),
            notes=data.get("notes"),
        )
        db.session.add(follow_up)

        if data.get("note_text"):
            db.session.add(
                DoctorNote(
                    doctor_id=doctor_id,
                    patient_id=patient_id,
                    lab_result_id=data.get("lab_result_id"),
                    note_text=data.get("note_text"),
                )
            )

        write_audit("DOCTOR_FOLLOWUP", "DoctorFollowUp", follow_up.id, actor_email, ip_address)
        db.session.commit()
        return follow_up

    @staticmethod
    def list_follow_ups(doctor_id, status=None):
        DoctorPortalService._get_profile_or_raise(doctor_id)
        query = DoctorFollowUp.query.filter_by(doctor_id=doctor_id)
        if status:
            query = query.filter(DoctorFollowUp.status == status)
        rows = query.order_by(DoctorFollowUp.follow_up_date.asc()).all()
        return {"count": len(rows), "follow_ups": [row.to_dict() for row in rows]}
