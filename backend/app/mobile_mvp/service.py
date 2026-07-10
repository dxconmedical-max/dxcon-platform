"""Mobile MVP service — Epic 7 patient and collector APIs."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any

from app.core.statuses import ASSIGNMENT_ASSIGNED
from app.extensions.db import db
from app.mobile_mvp.models import MobileAuditEvent, MobileDevice
from app.models.booking_assignment import BookingAssignment
from app.models.driver import Driver
from app.models.patient_profile import PatientProfile
from app.models.portal import PortalNotification
from app.models.user import User
from app.patient_marketplace.models import MpBooking, MpPayment, MpProvider
from app.patient_marketplace.service import BookingService, MarketplaceError, PaymentService
from app.reporting_engine.service import patient_released_reports
from app.services.collector_operations import CollectorOperationsError, CollectorOperationsService


class MobileMvpError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "MOBILE_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


MIN_APP_VERSION = "2.0.0"
RECOMMENDED_APP_VERSION = "2.0.0"


def _utcnow() -> datetime:
    return datetime.utcnow()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def write_mobile_audit(
    *,
    user_id: str | None,
    organization_id: str | None,
    workspace: str | None,
    event_type: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    outcome: str = "SUCCESS",
    correlation_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    event = MobileAuditEvent(
        user_id=user_id,
        organization_id=organization_id,
        workspace=workspace,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=outcome,
        correlation_id=correlation_id,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.session.add(event)


class MobileMvpService:
    @staticmethod
    def app_config() -> dict[str, Any]:
        return {
            "api_version": "v1",
            "min_supported_version": MIN_APP_VERSION,
            "recommended_version": RECOMMENDED_APP_VERSION,
            "forced_upgrade": False,
            "maintenance_message": None,
            "features": {
                "push_notifications": True,
                "offline_sync": True,
                "collector_tracking": True,
                "consultation_booking": True,
            },
        }

    @staticmethod
    def register_device(user_id: str, data: dict) -> dict:
        token = data.get("notification_token")
        device_ref = data.get("device_reference") or f"dev-{uuid.uuid4().hex[:12]}"
        existing = MobileDevice.query.filter_by(device_reference=device_ref).first()
        if existing and existing.user_id != user_id:
            raise MobileMvpError("Device belongs to another user", 403, "DEVICE_OWNERSHIP")
        device = existing or MobileDevice(device_reference=device_ref, user_id=user_id)
        device.organization_id = data.get("organization_id")
        device.platform = data.get("platform", "unknown")
        device.app_version = data.get("app_version")
        device.workspace = data.get("workspace")
        device.status = "ACTIVE"
        device.last_seen_at = _utcnow()
        if token:
            device.notification_token_hash = _hash_token(token)
        if not existing:
            db.session.add(device)
        db.session.commit()
        return device.to_dict()

    @staticmethod
    def revoke_device(user_id: str, device_id: str) -> dict:
        device = MobileDevice.query.filter_by(id=device_id, user_id=user_id).first()
        if not device:
            raise MobileMvpError("Device not found", 404)
        device.status = "REVOKED"
        device.revoked_at = _utcnow()
        device.notification_token_hash = None
        db.session.commit()
        return device.to_dict()

    @staticmethod
    def _patient_bookings_query(user_id: str, organization_id: str | None = None):
        query = MpBooking.query.filter_by(patient_user_id=user_id)
        if organization_id:
            query = query.filter_by(organization_id=organization_id)
        return query.order_by(MpBooking.created_at.desc())

    @staticmethod
    def patient_dashboard(user_id: str, organization_id: str | None = None) -> dict:
        bookings = MobileMvpService._patient_bookings_query(user_id, organization_id).limit(20).all()
        active = next(
            (b for b in bookings if b.booking_status not in ("COMPLETED", "CANCELLED", "REFUNDED")),
            None,
        )
        pending_payment = MpPayment.query.join(MpBooking).filter(
            MpBooking.patient_user_id == user_id,
            MpPayment.status.in_(("PENDING", "PROCESSING")),
        ).first()
        patient_code = MobileMvpService._resolve_patient_code(user_id)
        released = patient_released_reports(patient_code) if patient_code else []
        notifications = 0
        if patient_code:
            notifications = PortalNotification.query.filter_by(
                recipient_type="patient",
                recipient_id=patient_code,
                status="unread",
            ).count()
        return {
            "greeting_name": MobileMvpService._user_display_name(user_id),
            "recent_bookings": [b.to_dict() for b in bookings[:5]],
            "active_booking": active.to_dict() if active else None,
            "pending_payment": pending_payment.to_dict() if pending_payment else None,
            "released_reports_count": len(released),
            "released_reports_preview": released[:3],
            "unread_notifications": notifications,
            "quick_actions": [
                "book_test",
                "home_collection",
                "compare_providers",
                "view_results",
                "pay_invoice",
                "consultation",
            ],
        }

    @staticmethod
    def patient_bookings(user_id: str, organization_id: str | None = None) -> list[dict]:
        return [b.to_dict() for b in MobileMvpService._patient_bookings_query(user_id, organization_id).all()]

    @staticmethod
    def patient_booking_detail(user_id: str, booking_id: str) -> dict:
        booking = MpBooking.query.filter_by(id=booking_id, patient_user_id=user_id).first()
        if not booking:
            raise MobileMvpError("Booking not found", 404, "BOOKING_NOT_FOUND")
        payments = MpPayment.query.filter_by(booking_id=booking.id).all()
        timeline = MobileMvpService._booking_timeline(booking)
        return {
            "booking": booking.to_dict(),
            "payments": [p.to_dict() for p in payments],
            "timeline": timeline,
        }

    @staticmethod
    def patient_collector_tracking(user_id: str, booking_id: str) -> dict:
        booking = MpBooking.query.filter_by(id=booking_id, patient_user_id=user_id).first()
        if not booking:
            raise MobileMvpError("Booking not found", 404)
        if booking.booking_status not in (
            "COLLECTION_SCHEDULED",
            "PROVIDER_ACCEPTED",
            "SCHEDULED",
            "IN_PROGRESS",
            "CONFIRMED",
        ) and not booking.collection_job_id:
            return {"available": False, "reason": "Collector tracking not active for this booking"}
        assignment = None
        if booking.order_id:
            assignment = BookingAssignment.query.filter_by(booking_id=booking.order_id).order_by(
                BookingAssignment.created_at.desc()
            ).first()
        if not assignment:
            assignment = BookingAssignment.query.filter_by(booking_id=booking.id).order_by(
                BookingAssignment.created_at.desc()
            ).first()
        if not assignment:
            return {"available": False, "reason": "No collector assigned yet"}
        collector = Driver.query.get(assignment.collector_id)
        collector_name = None
        if collector and collector.full_name:
            parts = collector.full_name.split()
            collector_name = parts[0] if parts else "Collector"
        latest_gps = None
        if assignment.assignment_status in ("ACCEPTED", "IN_PROGRESS"):
            trail = CollectorOperationsService.get_gps_trail(assignment.collector_id, limit=1)
            if trail:
                latest_gps = trail[0].to_dict()
        return {
            "available": True,
            "collector_first_name": collector_name,
            "status": assignment.assignment_status,
            "eta_minutes": None,
            "location": latest_gps,
            "pickup_instructions": booking.pickup_address,
        }

    @staticmethod
    def patient_released_results(user_id: str) -> list[dict]:
        patient_code = MobileMvpService._resolve_patient_code(user_id)
        if not patient_code:
            return []
        reports = patient_released_reports(patient_code)
        return [r for r in reports if (r.get("report_status") or "").lower() == "released"]

    @staticmethod
    def patient_result_detail(user_id: str, report_code: str) -> dict:
        patient_code = MobileMvpService._resolve_patient_code(user_id)
        if not patient_code:
            raise MobileMvpError("Patient profile not linked", 404)
        if not is_report_visible_to_patient_report(match):
            raise MobileMvpError("Report not released", 403, "REPORT_NOT_RELEASED")
        reports = patient_released_reports(patient_code)
        match = next((r for r in reports if r.get("report_code") == report_code), None)
        if not match:
            raise MobileMvpError("Report not found", 404)
        write_mobile_audit(
            user_id=user_id,
            organization_id=None,
            workspace="patient",
            event_type="result_viewed",
            resource_type="ClinicalReport",
            resource_id=report_code,
        )
        db.session.commit()
        return match

    @staticmethod
    def patient_notifications(user_id: str) -> list[dict]:
        patient_code = MobileMvpService._resolve_patient_code(user_id)
        if not patient_code:
            return []
        rows = PortalNotification.query.filter_by(
            recipient_type="patient",
            recipient_id=patient_code,
        ).order_by(PortalNotification.created_at.desc()).limit(50).all()
        return [
            {
                "id": n.id,
                "category": n.event_type or "system",
                "title": n.title,
                "body": n.body,
                "status": n.status,
                "deep_link": None,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in rows
        ]

    @staticmethod
    def patient_family_profiles(user_id: str) -> list[dict]:
        patient_code = MobileMvpService._resolve_patient_code(user_id)
        if not patient_code:
            return []
        profile = PatientProfile.query.filter_by(patient_id=patient_code).first()
        if not profile or not profile.family_members_json:
            return [{"patient_code": patient_code, "relationship": "self", "authorized": True}]
        family = json.loads(profile.family_members_json or "[]")
        return [{"patient_code": patient_code, "relationship": "self", "authorized": True}, *family]

    @staticmethod
    def collector_dashboard(collector_id: str, user_id: str) -> dict:
        MobileMvpService._assert_collector_access(collector_id, user_id)
        jobs = CollectorOperationsService.list_jobs(collector_id)
        today = _utcnow().date()
        today_jobs = [
            j for j in jobs
            if j.get("booking", {}).get("scheduled_at") and str(today) in str(j["booking"].get("scheduled_at", ""))
        ]
        active = next((j for j in jobs if j["assignment"]["assignment_status"] in ("ACCEPTED", "IN_PROGRESS")), None)
        pending = [j for j in jobs if j["assignment"]["assignment_status"] == ASSIGNMENT_ASSIGNED]
        return {
            "today_jobs_count": len(today_jobs),
            "active_job": active,
            "pending_acceptance": pending[:10],
            "completed_count": len([j for j in jobs if j["assignment"]["assignment_status"] == "COMPLETED"]),
            "sync_status": "online",
        }

    @staticmethod
    def collector_jobs(collector_id: str, user_id: str, status: str | None = None) -> list[dict]:
        MobileMvpService._assert_collector_access(collector_id, user_id)
        return CollectorOperationsService.list_jobs(collector_id, status=status)

    @staticmethod
    def collector_job_detail(collector_id: str, user_id: str, assignment_id: str) -> dict:
        MobileMvpService._assert_collector_access(collector_id, user_id)
        assignment = BookingAssignment.query.get(assignment_id)
        if not assignment or assignment.collector_id != collector_id:
            raise MobileMvpError("Job not found", 404, "JOB_NOT_FOUND")
        jobs = CollectorOperationsService.list_jobs(collector_id)
        match = next((j for j in jobs if j["assignment"]["id"] == assignment_id), None)
        if not match:
            raise MobileMvpError("Job not found", 404)
        return match

    @staticmethod
    def reject_assignment(collector_id: str, user_id: str, assignment_id: str, reason: str) -> dict:
        MobileMvpService._assert_collector_access(collector_id, user_id)
        if not reason:
            raise MobileMvpError("Rejection reason required", 400, "REASON_REQUIRED")
        assignment = BookingAssignment.query.get(assignment_id)
        if not assignment or assignment.collector_id != collector_id:
            raise MobileMvpError("Assignment not found", 403)
        if assignment.assignment_status != ASSIGNMENT_ASSIGNED:
            raise MobileMvpError("Cannot reject assignment in current state", 409)
        assignment.assignment_status = "REJECTED"
        assignment.note = reason
        assignment.updated_at = _utcnow()
        write_mobile_audit(
            user_id=user_id,
            organization_id=None,
            workspace="collector",
            event_type="job_rejected",
            resource_type="BookingAssignment",
            resource_id=assignment_id,
            metadata={"reason": reason},
        )
        db.session.commit()
        return assignment.to_dict()

    @staticmethod
    def record_audit_batch(user_id: str, events: list[dict]) -> dict:
        for item in events[:50]:
            write_mobile_audit(
                user_id=user_id,
                organization_id=item.get("organization_id"),
                workspace=item.get("workspace"),
                event_type=item.get("event_type", "unknown"),
                resource_type=item.get("resource_type"),
                resource_id=item.get("resource_id"),
                outcome=item.get("outcome", "SUCCESS"),
                correlation_id=item.get("correlation_id"),
                metadata=item.get("metadata"),
            )
        db.session.commit()
        return {"recorded": min(len(events), 50)}

    @staticmethod
    def _booking_timeline(booking: MpBooking) -> list[dict]:
        events = [
            {"event": "booking_created", "at": booking.created_at.isoformat() if booking.created_at else None},
        ]
        status_map = {
            "PAYMENT_PENDING": "payment_pending",
            "CONFIRMED": "confirmed",
            "PROVIDER_ACCEPTED": "provider_accepted",
            "SCHEDULED": "collection_scheduled",
            "IN_PROGRESS": "in_progress",
            "COMPLETED": "completed",
            "CANCELLED": "cancelled",
        }
        if booking.booking_status in status_map:
            events.append({"event": status_map[booking.booking_status], "at": booking.updated_at.isoformat() if booking.updated_at else None})
        return events

    @staticmethod
    def _resolve_patient_code(user_id: str) -> str | None:
        user = User.query.get(user_id)
        if not user:
            return None
        from app.models.patient import Patient

        if user.phone:
            patient = Patient.query.filter_by(phone=user.phone).first()
            if patient:
                return patient.patient_code
        profile = PatientProfile.query.filter_by(patient_id=user.email).first()
        if profile:
            return profile.patient_id
        return None

    @staticmethod
    def _user_display_name(user_id: str) -> str:
        user = User.query.get(user_id)
        return (user.email.split("@")[0] if user and user.email else "Bạn")

    @staticmethod
    def _assert_collector_access(collector_id: str, user_id: str) -> None:
        collector = Driver.query.get(collector_id)
        if not collector:
            raise MobileMvpError("Collector not found", 404)
        user = User.query.get(user_id)
        if not user:
            raise MobileMvpError("Unauthorized", 401)
        if user.role in ("SUPER_ADMIN", "ADMIN"):
            return
        if collector.email and user.email and collector.email.lower() == user.email.lower():
            return
        if user.role in ("COLLECTOR", "DRIVER", "PARTNER_COLLECTOR"):
            return
        raise MobileMvpError("Not authorized for this collector profile", 403, "COLLECTOR_SCOPE")


def is_report_visible_to_patient_report(report: dict) -> bool:
    return (report.get("report_status") or "").lower() == "released" and report.get("is_visible_to_patient", True)
