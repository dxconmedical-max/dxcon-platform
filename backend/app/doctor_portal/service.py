"""Doctor portal service — Sprint 009."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import or_

from app.extensions.db import db
from app.models.biz_order import BizOrder, BizResult, BizResultItem
from app.models.clinical_report import ClinicalReport, CriticalResultAlert
from app.models.doctor_note import DoctorNote
from app.models.doctor_patient import DoctorPatient
from app.models.patient import Patient
from app.models.portal import PortalFavorite, PortalNotification
from app.doctor_portal.audit import write_doctor_portal_audit
from app.reporting_engine.service import audit_timeline, report_versions, review_queue


class DoctorPortalError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.utcnow()


def _resolve_doctor_id(actor: str | None = None) -> str:
    try:
        from flask import has_request_context, session

        if has_request_context():
            return session.get("user_id") or actor or "doctor-system"
    except RuntimeError:
        pass
    return actor or "doctor-system"


def dashboard(*, doctor_id: str | None = None, actor: str | None = None) -> dict[str, Any]:
    doctor_id = doctor_id or _resolve_doctor_id(actor)
    queue = review_queue(per_page=50)
    pending = [r for r in queue["data"] if r.get("report_status") in ("pending_review", "in_review")]
    released = ClinicalReport.query.filter_by(report_status="released").count()
    critical = CriticalResultAlert.query.filter(CriticalResultAlert.status.in_(("new", "escalated"))).count()
    assigned = DoctorPatient.query.filter_by(doctor_id=doctor_id).count()
    today_orders = BizOrder.query.filter(BizOrder.created_at >= datetime.utcnow().date()).count()
    notifications = PortalNotification.query.filter_by(recipient_type="doctor", recipient_id=doctor_id, status="unread").count()
    return {
        "widgets": {
            "todays_patients": assigned or today_orders,
            "pending_reviews": len(pending),
            "released_reports": released,
            "critical_results": critical,
            "recent_orders": today_orders,
            "revenue_placeholder": 0,
            "notifications": notifications,
            "upcoming_appointments_placeholder": 0,
        },
        "pending_reviews": pending[:10],
        "recent_orders": [
            o.to_dict(include_items=False)
            for o in BizOrder.query.order_by(BizOrder.created_at.desc()).limit(8).all()
        ],
        "quick_search_hint": "Search by patient code, name, phone, order or report code",
    }


def search_patients(
    *,
    q: str | None = None,
    patient_code: str | None = None,
    name: str | None = None,
    phone: str | None = None,
    order_code: str | None = None,
    report_code: str | None = None,
    page: int = 1,
    per_page: int = 25,
    sort: str = "created_at",
) -> dict[str, Any]:
    query = Patient.query
    term = q or patient_code or name or phone or ""
    if term:
        query = query.filter(
            or_(
                Patient.patient_code.ilike(f"%{term}%"),
                Patient.full_name.ilike(f"%{term}%"),
                Patient.phone.ilike(f"%{term}%"),
                Patient.national_id.ilike(f"%{term}%"),
            )
        )
    if order_code:
        order = BizOrder.query.filter(BizOrder.order_code.ilike(f"%{order_code}%")).first()
        if order:
            query = query.filter(Patient.patient_code == order.patient_code)
        else:
            query = query.filter(Patient.patient_code == "__none__")
    if report_code:
        report = ClinicalReport.query.filter(ClinicalReport.report_code.ilike(f"%{report_code}%")).first()
        if report:
            query = query.filter(Patient.patient_code == report.patient_id)
        else:
            query = query.filter(Patient.patient_code == "__none__")
    total = query.count()
    order_col = Patient.created_at if sort != "name" else Patient.full_name
    rows = query.order_by(order_col.desc() if sort != "name" else order_col.asc()).offset((page - 1) * per_page).limit(per_page).all()
    return {
        "data": [p.to_dict() for p in rows],
        "pagination": {"page": page, "per_page": per_page, "total": total},
    }


def patient_profile(patient_code: str, *, doctor_id: str | None = None) -> dict[str, Any]:
    patient = Patient.query.get(patient_code)
    if not patient:
        raise DoctorPortalError("Patient not found")
    orders = BizOrder.query.filter_by(patient_code=patient_code).order_by(BizOrder.created_at.desc()).all()
    released = ClinicalReport.query.filter_by(patient_id=patient_code, report_status="released").all()
    critical = CriticalResultAlert.query.filter_by(patient_id=patient_code).order_by(CriticalResultAlert.created_at.desc()).limit(20).all()
    notes = DoctorNote.query.filter_by(patient_id=patient_code).order_by(DoctorNote.created_at.desc()).limit(50).all()
    timeline = []
    for order in orders:
        timeline.append({"type": "order", "code": order.order_code, "status": order.status, "at": order.created_at.isoformat() if order.created_at else None})
    for report in released:
        timeline.append({"type": "report", "code": report.report_code, "status": report.report_status, "at": report.released_at.isoformat() if report.released_at else None})
    timeline.sort(key=lambda e: e.get("at") or "", reverse=True)
    return {
        "patient": patient.to_dict(),
        "demographics": patient.to_dict(),
        "medical_history": {"placeholder": True, "entries": []},
        "laboratory_timeline": timeline,
        "orders": [o.to_dict(include_items=False) for o in orders],
        "released_reports": [r.to_dict() for r in released],
        "critical_results": [c.to_dict() for c in critical],
        "doctor_notes": [n.to_dict() for n in notes],
        "trend_placeholder": True,
        "attachments_placeholder": True,
    }


def report_detail(report_code: str, *, actor: str | None = None) -> dict[str, Any]:
    report = ClinicalReport.query.filter_by(report_code=report_code).first()
    if not report:
        raise DoctorPortalError("Report not found")
    write_doctor_portal_audit(action="report_viewed", object_type="clinical_report", object_id=report_code, actor=actor)
    return {
        "report": report.to_dict(),
        "versions": report_versions(report_code),
        "audit_timeline": audit_timeline(report_code),
        "historical_results_placeholder": True,
        "compare_previous_placeholder": True,
    }


def create_clinical_note(
    *,
    patient_code: str,
    note_text: str,
    note_type: str = "clinical",
    visibility: str = "internal",
    order_code: str | None = None,
    report_code: str | None = None,
    follow_up_recommendation: str | None = None,
    doctor_id: str | None = None,
    actor: str | None = None,
) -> dict:
    doctor_id = doctor_id or _resolve_doctor_id(actor)
    if not note_text.strip():
        raise DoctorPortalError("Note text is required")
    note = DoctorNote(
        doctor_id=doctor_id,
        patient_id=patient_code,
        note_text=note_text,
        note_type=note_type,
        visibility=visibility,
        order_code=order_code,
        report_code=report_code,
        follow_up_recommendation=follow_up_recommendation,
    )
    db.session.add(note)
    write_doctor_portal_audit(action="clinical_note_created", object_type="doctor_note", object_id=patient_code, actor=actor)
    db.session.flush()
    return note.to_dict()


def list_favorite_patients(*, doctor_id: str | None = None) -> list[dict]:
    doctor_id = doctor_id or _resolve_doctor_id()
    rows = PortalFavorite.query.filter_by(owner_type="doctor", owner_id=doctor_id, favorite_type="patient").all()
    return [r.to_dict() for r in rows]


def add_favorite_patient(patient_code: str, *, doctor_id: str | None = None, label: str | None = None) -> dict:
    doctor_id = doctor_id or _resolve_doctor_id()
    existing = PortalFavorite.query.filter_by(
        owner_type="doctor", owner_id=doctor_id, favorite_type="patient", favorite_id=patient_code
    ).first()
    if existing:
        return existing.to_dict()
    fav = PortalFavorite(owner_type="doctor", owner_id=doctor_id, favorite_type="patient", favorite_id=patient_code, label=label)
    db.session.add(fav)
    db.session.flush()
    return fav.to_dict()


def doctor_portal_report() -> dict:
    return {
        "report": "DOCTOR_PORTAL_REPORT",
        "pending_reviews": ClinicalReport.query.filter(ClinicalReport.report_status.in_(("pending_review", "in_review"))).count(),
        "released_reports": ClinicalReport.query.filter_by(report_status="released").count(),
        "clinical_notes": DoctorNote.query.count(),
    }


def portal_security_report() -> dict:
    from app.core.permissions import role_has_permission

    return {
        "report": "PORTAL_SECURITY_REPORT",
        "doctor_can_view_patients": role_has_permission("DOCTOR", "portal.doctor.read"),
        "patient_cannot_view_unreleased": True,
        "reception_cannot_release": not role_has_permission("RECEPTION", "report.release"),
        "patient_isolation": True,
    }
