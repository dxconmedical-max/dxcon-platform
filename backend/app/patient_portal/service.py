"""Patient portal service — Sprint 009."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any

from flask import session

from app.business_engine import service as biz
from app.business_engine.service import BusinessEngineError
from app.extensions.db import db
from app.models.biz_order import BizInvoice, BizOrder, BizPayment
from app.models.clinical_report import ClinicalReport, CriticalResultAlert
from app.models.doctor_note import DoctorNote
from app.models.patient import Patient
from app.models.patient_consent import PatientConsent
from app.models.patient_profile import PatientProfile
from app.models.portal import PortalFavorite, PortalNotification, PortalQrToken
from app.patient_portal.audit import write_patient_portal_audit
from app.reporting_engine.service import audit_timeline, is_report_visible_to_patient, patient_released_reports, report_versions


class PatientPortalError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.utcnow()


def _session_patient_code() -> str | None:
    code = session.get("patient_code")
    if code:
        return code
    user_id = session.get("user_id")
    if user_id:
        patient = Patient.query.filter_by(id=user_id).first() or Patient.query.get(user_id)
        if patient:
            return patient.patient_code
    return None


def _require_patient_access(patient_code: str) -> None:
    role = session.get("role") or ""
    if role in ("SUPER_ADMIN", "ADMIN"):
        return
    if role == "PATIENT":
        own = _session_patient_code()
        if own and own != patient_code:
            raise PatientPortalError("Cannot access another patient's data")
        profile = PatientProfile.query.filter_by(patient_id=patient_code).first()
        if profile and profile.family_members_json:
            family = json.loads(profile.family_members_json or "[]")
            allowed = {patient_code, own} | {m.get("patient_code") for m in family if m.get("patient_code")}
            if own and patient_code not in allowed:
                raise PatientPortalError("Not authorized for this family profile")


def _ensure_profile(patient_code: str) -> PatientProfile:
    profile = PatientProfile.query.filter_by(patient_id=patient_code).first()
    if profile:
        return profile
    profile = PatientProfile(patient_id=patient_code, qr_code=f"PQR-{patient_code}")
    db.session.add(profile)
    db.session.flush()
    return profile


def dashboard(*, patient_code: str | None = None, actor: str | None = None) -> dict[str, Any]:
    patient_code = patient_code or _session_patient_code()
    if not patient_code:
        raise PatientPortalError("Patient session required")
    _require_patient_access(patient_code)
    try:
        portal = biz.get_patient_portal_data(patient_code)
    except BusinessEngineError:
        patient = Patient.query.get(patient_code)
        if not patient:
            raise PatientPortalError("Patient not found")
        portal = {"patient": patient.to_dict(), "orders": [], "invoices": [], "released_reports": []}
    released = patient_released_reports(patient_code)
    portal["released_reports"] = released
    outstanding = sum(
        inv.get("total_amount", 0) or inv.get("amount", 0)
        for inv in portal.get("invoices", [])
        if (inv.get("status") or "").lower() not in ("paid", "completed")
    )
    notifications = PortalNotification.query.filter_by(recipient_type="patient", recipient_id=patient_code, status="unread").count()
    profile = _ensure_profile(patient_code)
    completion = 0
    patient = portal["patient"]
    for field in ("phone", "email", "gender"):
        if patient.get(field):
            completion += 33
    return {
        "patient": patient,
        "widgets": {
            "recent_reports": len(released),
            "recent_orders": len(portal.get("orders", [])),
            "invoices": len(portal.get("invoices", [])),
            "outstanding_balance": outstanding,
            "notifications": notifications,
            "upcoming_collection_placeholder": 0,
            "profile_completion": min(completion, 100),
        },
        "recent_reports": released[:5],
        "recent_orders": portal.get("orders", [])[:5],
        "invoices": portal.get("invoices", [])[:5],
        "profile": profile.to_dict(),
    }


def medical_history(*, patient_code: str | None = None, event_type: str | None = None) -> dict[str, Any]:
    patient_code = patient_code or _session_patient_code()
    if not patient_code:
        raise PatientPortalError("Patient session required")
    _require_patient_access(patient_code)
    orders = BizOrder.query.filter_by(patient_code=patient_code).order_by(BizOrder.created_at.desc()).all()
    reports = patient_released_reports(patient_code)
    invoices = []
    for order in orders:
        inv = BizInvoice.query.filter_by(order_id=order.id).first()
        if inv:
            pay = BizPayment.query.filter_by(invoice_id=inv.id).first()
            invoices.append({**inv.to_dict(), "order_code": order.order_code, "payment": pay.to_dict() if pay else None})
    notes = DoctorNote.query.filter_by(patient_id=patient_code, visibility="patient_visible").order_by(DoctorNote.created_at.desc()).all()
    critical = CriticalResultAlert.query.filter_by(patient_id=patient_code).all()
    events = []
    for o in orders:
        events.append({"event_type": "order", "title": o.order_code, "status": o.status, "at": o.created_at.isoformat() if o.created_at else None})
    for r in reports:
        events.append({"event_type": "report", "title": r["report_code"], "status": r["report_status"], "at": r.get("released_at")})
    for inv in invoices:
        events.append({"event_type": "invoice", "title": inv.get("invoice_no", ""), "status": inv.get("status"), "at": inv.get("created_at")})
    for n in notes:
        events.append({"event_type": "doctor_note", "title": "Clinical note", "status": n.note_type if hasattr(n, "note_type") else "note", "at": n.created_at.isoformat() if n.created_at else None})
    if event_type:
        events = [e for e in events if e["event_type"] == event_type]
    events.sort(key=lambda e: e.get("at") or "", reverse=True)
    return {
        "timeline": events,
        "orders": [o.to_dict(include_items=False) for o in orders],
        "reports": reports,
        "invoices": invoices,
        "doctor_notes": [n.to_dict() for n in notes],
        "critical_history": [c.to_dict() for c in critical],
    }


def get_report(report_code: str, *, patient_code: str | None = None, actor: str | None = None) -> dict[str, Any]:
    patient_code = patient_code or _session_patient_code()
    report = ClinicalReport.query.filter_by(report_code=report_code).first()
    if not report:
        raise PatientPortalError("Report not found")
    if patient_code:
        _require_patient_access(patient_code)
        if report.patient_id != patient_code:
            raise PatientPortalError("Report not available")
    if not is_report_visible_to_patient(report):
        raise PatientPortalError("Report not released")
    write_patient_portal_audit(action="report_viewed", object_type="clinical_report", object_id=report_code, actor=actor)
    return {
        "report": report.to_dict(),
        "versions": report_versions(report_code),
        "audit_timeline": audit_timeline(report_code),
        "qr_payload": report.qr_payload,
        "html_content": report.html_content,
    }


def list_invoices(*, patient_code: str | None = None, actor: str | None = None) -> dict[str, Any]:
    patient_code = patient_code or _session_patient_code()
    if not patient_code:
        raise PatientPortalError("Patient session required")
    _require_patient_access(patient_code)
    write_patient_portal_audit(action="invoice_viewed", object_type="patient", object_id=patient_code, actor=actor)
    history = medical_history(patient_code=patient_code)
    return {"invoices": history["invoices"], "transactions": history["invoices"]}


def update_profile(data: dict, *, patient_code: str | None = None, actor: str | None = None) -> dict:
    patient_code = patient_code or _session_patient_code()
    if not patient_code:
        raise PatientPortalError("Patient session required")
    _require_patient_access(patient_code)
    patient = Patient.query.get(patient_code)
    if not patient:
        raise PatientPortalError("Patient not found")
    profile = _ensure_profile(patient_code)
    allowed_patient = {"phone", "email"}
    for field in allowed_patient:
        if field in data:
            setattr(patient, field, data[field])
    for field in ("avatar_url", "language", "timezone", "emergency_contact_name", "emergency_contact_phone"):
        if field in data:
            setattr(profile, field, data[field])
    if "notification_preference" in data:
        prefs = json.loads(profile.favorite_doctors_json or "[]")  # reuse json column pattern
        _ = prefs
    write_patient_portal_audit(action="profile_updated", object_type="patient_profile", object_id=patient_code, actor=actor)
    db.session.flush()
    return {"patient": patient.to_dict(), "profile": profile.to_dict()}


def generate_qr_health_card(*, patient_code: str | None = None, organization_id: str | None = None, actor: str | None = None) -> dict:
    patient_code = patient_code or _session_patient_code()
    if not patient_code:
        raise PatientPortalError("Patient session required")
    _require_patient_access(patient_code)
    token = hashlib.sha256(f"{patient_code}:{uuid.uuid4().hex}".encode()).hexdigest()[:32]
    payload = json.dumps({
        "patient_code": patient_code,
        "organization_id": organization_id or "default",
        "verification_token": token,
        "type": "dxcon_health_card",
    })
    row = PortalQrToken(
        patient_id=patient_code,
        verification_token=token,
        organization_id=organization_id,
        qr_payload=payload,
        expires_at=_utcnow() + timedelta(days=365),
    )
    db.session.add(row)
    profile = _ensure_profile(patient_code)
    profile.qr_payload = payload
    profile.qr_code = f"QR-{patient_code}"
    write_patient_portal_audit(action="qr_generated", object_type="portal_qr", object_id=patient_code, actor=actor)
    db.session.flush()
    return {"qr_payload": payload, "verification_token": token, "patient_code": patient_code}


def list_notifications(*, patient_code: str | None = None) -> dict:
    patient_code = patient_code or _session_patient_code()
    if not patient_code:
        raise PatientPortalError("Patient session required")
    rows = PortalNotification.query.filter_by(recipient_type="patient", recipient_id=patient_code).order_by(
        PortalNotification.created_at.desc()
    ).limit(50).all()
    return {"data": [r.to_dict() for r in rows]}


def grant_consent(consent_type: str, *, patient_code: str | None = None, actor: str | None = None, metadata: dict | None = None) -> dict:
    patient_code = patient_code or _session_patient_code()
    if not patient_code:
        raise PatientPortalError("Patient session required")
    row = PatientConsent(
        patient_id=patient_code,
        consent_type=consent_type,
        status="GRANTED",
        granted_at=_utcnow(),
        metadata_json=json.dumps(metadata or {}),
    )
    db.session.add(row)
    write_patient_portal_audit(action="consent_granted", object_type="patient_consent", object_id=consent_type, actor=actor)
    db.session.flush()
    return row.to_dict()


def revoke_consent(consent_type: str, *, patient_code: str | None = None, actor: str | None = None) -> dict:
    patient_code = patient_code or _session_patient_code()
    if not patient_code:
        raise PatientPortalError("Patient session required")
    row = PatientConsent(
        patient_id=patient_code,
        consent_type=consent_type,
        status="REVOKED",
        revoked_at=_utcnow(),
    )
    db.session.add(row)
    write_patient_portal_audit(action="consent_revoked", object_type="patient_consent", object_id=consent_type, actor=actor)
    db.session.flush()
    return row.to_dict()


def list_consents(*, patient_code: str | None = None) -> list[dict]:
    patient_code = patient_code or _session_patient_code()
    if not patient_code:
        raise PatientPortalError("Patient session required")
    return [c.to_dict() for c in PatientConsent.query.filter_by(patient_id=patient_code).order_by(PatientConsent.created_at.desc()).all()]


def add_favorite(favorite_type: str, favorite_id: str, *, patient_code: str | None = None, label: str | None = None) -> dict:
    patient_code = patient_code or _session_patient_code()
    if not patient_code:
        raise PatientPortalError("Patient session required")
    fav = PortalFavorite(
        owner_type="patient",
        owner_id=patient_code,
        favorite_type=favorite_type,
        favorite_id=favorite_id,
        label=label,
    )
    db.session.add(fav)
    db.session.flush()
    return fav.to_dict()


def list_favorites(*, patient_code: str | None = None) -> list[dict]:
    patient_code = patient_code or _session_patient_code()
    if not patient_code:
        raise PatientPortalError("Patient session required")
    rows = PortalFavorite.query.filter_by(owner_type="patient", owner_id=patient_code).all()
    return [r.to_dict() for r in rows]


def patient_portal_report() -> dict:
    return {
        "report": "PATIENT_PORTAL_REPORT",
        "released_reports": ClinicalReport.query.filter_by(report_status="released", is_visible_to_patient=True).count(),
        "portal_notifications": PortalNotification.query.count(),
        "qr_tokens": PortalQrToken.query.count(),
    }
