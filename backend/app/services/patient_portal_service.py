import json
import uuid
from datetime import datetime

from app.core.audit import write_audit
from app.core.statuses import (
    LAB_RESULT_RELEASED,
    PATIENT_CONSENT_GRANTED,
    PATIENT_CONSENT_REVOKED,
)
from app.extensions.db import db
from app.models.lab_result import LabResult
from app.models.marketplace_booking import MarketplaceBooking
from app.models.medical_order import MedicalOrder
from app.models.notification import Notification
from app.models.notification_recipient import NotificationRecipient
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.patient import Patient
from app.models.patient_consent import PatientConsent
from app.models.patient_device import PatientDevice
from app.models.patient_notification_setting import PatientNotificationSetting
from app.models.patient_preference import PatientPreference
from app.models.patient_profile import PatientProfile
from app.models.result_file import ResultFile
from app.models.result_release import ResultRelease
from app.models.result_timeline import ResultTimeline
from app.models.test_result import TestResult


class PatientPortalError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class PatientPortalService:

    @staticmethod
    def _get_patient_or_raise(patient_id):
        patient = Patient.query.get(patient_id)
        if not patient:
            raise PatientPortalError("Patient not found", 404)
        return patient

    @staticmethod
    def _ensure_profile(patient_id):
        profile = PatientProfile.query.filter_by(patient_id=patient_id).first()
        if profile:
            return profile
        patient = PatientPortalService._get_patient_or_raise(patient_id)
        qr_code = f"PQR-{patient.patient_code}"
        profile = PatientProfile(
            patient_id=patient.id,
            qr_code=qr_code,
            qr_payload=json.dumps(
                {
                    "patient_id": patient.id,
                    "patient_code": patient.patient_code,
                    "full_name": patient.full_name,
                }
            ),
        )
        db.session.add(profile)
        db.session.commit()
        return profile

    @staticmethod
    def _patient_orders_query(patient_id):
        patient = PatientPortalService._get_patient_or_raise(patient_id)
        legacy_orders = Order.query.filter_by(patient_id=patient_id).all()
        medical_orders = MedicalOrder.query.filter(
            db.or_(
                MedicalOrder.patient_id == patient_id,
                MedicalOrder.patient_phone == patient.phone,
                MedicalOrder.patient_name == patient.full_name,
            )
        ).all()
        return legacy_orders, medical_orders

    @staticmethod
    def _patient_bookings(patient):
        if not patient.phone:
            return []
        return MarketplaceBooking.query.filter(
            db.or_(
                MarketplaceBooking.patient_phone == patient.phone,
                MarketplaceBooking.patient_name == patient.full_name,
            )
        ).order_by(MarketplaceBooking.created_at.desc()).all()


class PatientDashboardService:

    @staticmethod
    def get_dashboard(patient_id):
        patient = PatientPortalService._get_patient_or_raise(patient_id)
        profile = PatientPortalService._ensure_profile(patient_id)
        legacy_orders, medical_orders = PatientPortalService._patient_orders_query(patient_id)
        bookings = PatientPortalService._patient_bookings(patient)

        lab_results = []
        if medical_orders:
            order_ids = [order.id for order in medical_orders]
            lab_results = (
                LabResult.query.filter(LabResult.medical_order_id.in_(order_ids))
                .order_by(LabResult.created_at.desc())
                .all()
            )

        released_results = [result for result in lab_results if result.status == LAB_RESULT_RELEASED]
        notifications = PatientPortalService.get_notifications(patient_id)

        return {
            "patient": patient.to_dict(),
            "profile": profile.to_dict(),
            "summary": {
                "appointments_total": len(bookings),
                "orders_total": len(legacy_orders) + len(medical_orders),
                "results_total": len(lab_results),
                "released_results_total": len(released_results),
                "notifications_unread": len(
                    [item for item in notifications.get("notifications", []) if item.get("status") != "DELIVERED"]
                ),
            },
            "recent_orders": [
                order.to_dict()
                for order in sorted(
                    medical_orders,
                    key=lambda row: row.created_at or datetime.min,
                    reverse=True,
                )[:5]
            ],
            "recent_results": [result.to_dict(include_items=False) for result in lab_results[:5]],
        }


class MedicalHistoryService:

    @staticmethod
    def list_appointments(patient_id):
        patient = PatientPortalService._get_patient_or_raise(patient_id)
        bookings = PatientPortalService._patient_bookings(patient)
        return {
            "count": len(bookings),
            "appointments": [booking.to_dict() for booking in bookings],
        }

    @staticmethod
    def list_orders(patient_id):
        legacy_orders, medical_orders = PatientPortalService._patient_orders_query(patient_id)
        payload = []
        for order in legacy_orders:
            item = order.to_dict()
            item["order_type"] = "LEGACY"
            payload.append(item)
        for order in medical_orders:
            item = order.to_dict()
            item["order_type"] = "MEDICAL"
            payload.append(item)
        payload.sort(key=lambda row: row.get("created_at") or "", reverse=True)
        return {"count": len(payload), "orders": payload}

    @staticmethod
    def list_results(patient_id):
        patient = PatientPortalService._get_patient_or_raise(patient_id)
        _, medical_orders = PatientPortalService._patient_orders_query(patient_id)
        results_payload = []

        if medical_orders:
            order_ids = [order.id for order in medical_orders]
            lab_results = LabResult.query.filter(LabResult.medical_order_id.in_(order_ids)).all()
            for result in lab_results:
                row = result.to_dict(include_items=True, include_attachments=True)
                release = (
                    ResultRelease.query.filter_by(lab_result_id=result.id)
                    .order_by(ResultRelease.released_at.desc())
                    .first()
                )
                row["download_url"] = f"/results/report/{result.medical_order_id}/pdf"
                row["share_ready"] = result.status == LAB_RESULT_RELEASED
                row["release"] = release.to_dict() if release else None
                results_payload.append(row)

        legacy_orders, _ = PatientPortalService._patient_orders_query(patient_id)
        for order in legacy_orders:
            items = OrderItem.query.filter_by(order_id=order.id).all()
            for item in items:
                test_result = TestResult.query.filter_by(order_item_id=item.id).first()
                if test_result:
                    results_payload.append(
                        {
                            "source": "LEGACY",
                            "order_id": order.id,
                            "order_code": order.order_code,
                            "result": test_result.to_dict(),
                            "download_url": f"/results/report/{order.id}/pdf",
                        }
                    )

            files = ResultFile.query.filter_by(order_id=order.id).all()
            for result_file in files:
                results_payload.append(
                    {
                        "source": "RESULT_FILE",
                        "order_id": order.id,
                        "order_code": order.order_code,
                        "file": result_file.to_dict(),
                        "download_url": f"/portal/result-files/download/{result_file.id}",
                    }
                )

        return {"count": len(results_payload), "results": results_payload}

    @staticmethod
    def get_profile(patient_id):
        patient = PatientPortalService._get_patient_or_raise(patient_id)
        profile = PatientPortalService._ensure_profile(patient_id)
        preferences = PatientPreference.query.filter_by(patient_id=patient_id).all()
        devices = PatientDevice.query.filter_by(patient_id=patient_id, is_active=True).all()
        notification_settings = PatientNotificationSetting.query.filter_by(patient_id=patient_id).all()
        consents = PatientConsent.query.filter_by(patient_id=patient_id).all()

        return {
            "patient": patient.to_dict(),
            "profile": profile.to_dict(),
            "preferences": [row.to_dict() for row in preferences],
            "devices": [row.to_dict() for row in devices],
            "notification_settings": [row.to_dict() for row in notification_settings],
            "consents": [row.to_dict() for row in consents],
            "favorite_doctors": json.loads(profile.favorite_doctors_json or "[]"),
            "favorite_clinics": json.loads(profile.favorite_clinics_json or "[]"),
            "family_members": json.loads(profile.family_members_json or "[]"),
            "qr_profile": {
                "qr_code": profile.qr_code,
                "qr_payload": profile.qr_payload,
            },
        }

    @staticmethod
    def update_profile(patient_id, data, actor_email="SYSTEM", ip_address=""):
        patient = PatientPortalService._get_patient_or_raise(patient_id)
        profile = PatientPortalService._ensure_profile(patient_id)

        for field in ["full_name", "gender", "date_of_birth", "phone", "email", "address", "national_id"]:
            if field in data:
                setattr(patient, field, data[field])

        for field in [
            "avatar_url",
            "language",
            "timezone",
            "emergency_contact_name",
            "emergency_contact_phone",
        ]:
            if field in data:
                setattr(profile, field, data[field])

        if "favorite_doctors" in data:
            profile.favorite_doctors_json = json.dumps(data["favorite_doctors"])
        if "favorite_clinics" in data:
            profile.favorite_clinics_json = json.dumps(data["favorite_clinics"])
        if "family_members" in data:
            profile.family_members_json = json.dumps(data["family_members"])

        for pref in data.get("preferences", []):
            row = PatientPreference.query.filter_by(
                patient_id=patient_id,
                pref_key=pref.get("pref_key"),
            ).first()
            if not row:
                row = PatientPreference(
                    patient_id=patient_id,
                    pref_key=pref.get("pref_key"),
                )
                db.session.add(row)
            row.pref_value = pref.get("pref_value")

        write_audit("PATIENT_PROFILE_UPDATE", "PatientProfile", profile.id, actor_email, ip_address)
        db.session.commit()
        return MedicalHistoryService.get_profile(patient_id)


class TimelineService:

    @staticmethod
    def get_timeline(patient_id):
        patient = PatientPortalService._get_patient_or_raise(patient_id)
        events = []

        for booking in PatientPortalService._patient_bookings(patient):
            events.append(
                {
                    "event_type": "APPOINTMENT",
                    "reference_id": booking.id,
                    "title": f"Appointment {booking.booking_code}",
                    "status": booking.status,
                    "occurred_at": booking.created_at.isoformat() if booking.created_at else None,
                }
            )

        _, medical_orders = PatientPortalService._patient_orders_query(patient_id)
        for order in medical_orders:
            events.append(
                {
                    "event_type": "ORDER",
                    "reference_id": order.id,
                    "title": f"Order {order.order_code}",
                    "status": order.status,
                    "occurred_at": order.created_at.isoformat() if order.created_at else None,
                }
            )

        if medical_orders:
            order_ids = [order.id for order in medical_orders]
            lab_results = LabResult.query.filter(LabResult.medical_order_id.in_(order_ids)).all()
            for result in lab_results:
                events.append(
                    {
                        "event_type": "LAB_RESULT",
                        "reference_id": result.id,
                        "title": f"Result {result.result_code}",
                        "status": result.status,
                        "occurred_at": result.created_at.isoformat() if result.created_at else None,
                    }
                )
                timeline_rows = (
                    ResultTimeline.query.filter_by(lab_result_id=result.id)
                    .order_by(ResultTimeline.created_at.asc())
                    .all()
                )
                for row in timeline_rows:
                    events.append(
                        {
                            "event_type": row.event_type,
                            "reference_id": result.id,
                            "title": row.message or row.event_type,
                            "status": row.to_status or result.status,
                            "occurred_at": row.created_at.isoformat() if row.created_at else None,
                        }
                    )

        events.sort(key=lambda row: row.get("occurred_at") or "", reverse=True)
        return {"count": len(events), "timeline": events}


class ConsentService:

    @staticmethod
    def list_consents(patient_id):
        PatientPortalService._get_patient_or_raise(patient_id)
        rows = PatientConsent.query.filter_by(patient_id=patient_id).order_by(
            PatientConsent.created_at.desc()
        ).all()
        return {"count": len(rows), "consents": [row.to_dict() for row in rows]}

    @staticmethod
    def record_consent(patient_id, data, actor_email="SYSTEM", ip_address=""):
        PatientPortalService._get_patient_or_raise(patient_id)
        consent_type = data.get("consent_type")
        if not consent_type:
            raise PatientPortalError("consent_type is required", 400)

        granted = data.get("granted", True)
        row = PatientConsent(
            patient_id=patient_id,
            consent_type=consent_type,
            consent_version=data.get("consent_version", "1.0"),
            status=PATIENT_CONSENT_GRANTED if granted else PATIENT_CONSENT_REVOKED,
            granted_at=datetime.utcnow() if granted else None,
            revoked_at=None if granted else datetime.utcnow(),
            ip_address=ip_address or data.get("ip_address"),
            metadata_json=json.dumps(data.get("metadata") or {}),
        )
        db.session.add(row)
        write_audit("PATIENT_CONSENT", "PatientConsent", row.id, actor_email, ip_address)
        db.session.commit()
        return row.to_dict()


class PatientPortalServiceExtended(PatientPortalService):

    @staticmethod
    def get_notifications(patient_id):
        patient = PatientPortalService._get_patient_or_raise(patient_id)
        recipients = NotificationRecipient.query.filter(
            db.or_(
                NotificationRecipient.recipient_id == patient_id,
                NotificationRecipient.email == patient.email,
                NotificationRecipient.phone == patient.phone,
            )
        ).all()
        if not recipients:
            return {"count": 0, "notifications": []}

        notification_ids = [row.notification_id for row in recipients]
        notifications = (
            Notification.query.filter(Notification.id.in_(notification_ids))
            .order_by(Notification.created_at.desc())
            .all()
        )
        return {
            "count": len(notifications),
            "notifications": [row.to_dict() for row in notifications],
        }

    @staticmethod
    def share_report(patient_id, data, actor_email="SYSTEM", ip_address=""):
        PatientPortalService._get_patient_or_raise(patient_id)
        lab_result_id = data.get("lab_result_id")
        order_id = data.get("order_id")
        if not lab_result_id and not order_id:
            raise PatientPortalError("lab_result_id or order_id is required", 400)

        share_code = f"SHR-{uuid.uuid4().hex[:10].upper()}"
        share_url = data.get("share_url")
        if lab_result_id:
            result = LabResult.query.get(lab_result_id)
            if not result:
                raise PatientPortalError("Lab result not found", 404)
            if result.status != LAB_RESULT_RELEASED:
                raise PatientPortalError("Only released results can be shared", 409)
            share_url = share_url or f"/results/{lab_result_id}?share={share_code}"
        else:
            share_url = share_url or f"/results/report/{order_id}?share={share_code}"

        ConsentService.record_consent(
            patient_id,
            {
                "consent_type": "RESULT_SHARING",
                "granted": True,
                "metadata": {
                    "share_code": share_code,
                    "lab_result_id": lab_result_id,
                    "order_id": order_id,
                },
            },
            actor_email=actor_email,
            ip_address=ip_address,
        )

        return {
            "share_code": share_code,
            "share_url": share_url,
            "expires_in_hours": data.get("expires_in_hours", 72),
        }


PatientPortalService.get_notifications = PatientPortalServiceExtended.get_notifications
PatientPortalService.share_report = PatientPortalServiceExtended.share_report
