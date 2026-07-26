"""Sprint 008 — Clinical reporting engine models."""

from __future__ import annotations

from datetime import datetime
import uuid

from app.extensions.db import db

REPORT_STATUSES = (
    "draft",
    "pending_review",
    "in_review",
    "approved",
    "released",
    "rejected",
    "amended",
    "cancelled",
)

SIGNATURE_METHODS = ("INTERNAL_APPROVAL", "PASSWORD_CONFIRMATION", "FUTURE_DIGITAL_CERTIFICATE")
NOTIFICATION_CHANNELS = ("EMAIL", "SMS", "ZALO", "IN_APP", "WEBHOOK")
CRITICAL_STATUSES = ("new", "acknowledged", "escalated", "resolved")


class ClinicalReport(db.Model):
    __tablename__ = "clinical_reports"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    order_id = db.Column(db.String(36), nullable=False, index=True)
    order_code = db.Column(db.String(50), nullable=False, index=True)
    patient_id = db.Column(db.String(50), nullable=False, index=True)
    accession_id = db.Column(db.String(36))
    accession_number = db.Column(db.String(50))
    organization_id = db.Column(db.String(36))
    laboratory_id = db.Column(db.String(36))
    result_id = db.Column(db.String(36))
    report_status = db.Column(db.String(30), nullable=False, default="draft", index=True)
    report_version = db.Column(db.Integer, nullable=False, default=1)
    report_type = db.Column(db.String(30), default="diagnostic")
    generated_at = db.Column(db.DateTime)
    approved_by = db.Column(db.String(255))
    approved_at = db.Column(db.DateTime)
    released_by = db.Column(db.String(255))
    released_at = db.Column(db.DateTime)
    doctor_note = db.Column(db.Text)
    lab_note = db.Column(db.Text)
    clinical_summary = db.Column(db.Text)
    pdf_path = db.Column(db.String(500))
    report_hash = db.Column(db.String(128))
    qr_payload = db.Column(db.String(255))
    html_content = db.Column(db.Text)
    is_visible_to_patient = db.Column(db.Boolean, default=False)
    amended_from_report_id = db.Column(db.String(36))
    amendment_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "report_code": self.report_code,
            "order_id": self.order_id,
            "order_code": self.order_code,
            "patient_id": self.patient_id,
            "accession_number": self.accession_number,
            "organization_id": self.organization_id,
            "laboratory_id": self.laboratory_id,
            "result_id": self.result_id,
            "report_status": self.report_status,
            "report_version": self.report_version,
            "report_type": self.report_type,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "released_by": self.released_by,
            "released_at": self.released_at.isoformat() if self.released_at else None,
            "doctor_note": self.doctor_note,
            "lab_note": self.lab_note,
            "clinical_summary": self.clinical_summary,
            "pdf_path": self.pdf_path,
            "report_hash": self.report_hash,
            "qr_payload": self.qr_payload,
            "is_visible_to_patient": self.is_visible_to_patient,
            "amended_from_report_id": self.amended_from_report_id,
            "amendment_reason": self.amendment_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ReportDigitalSignature(db.Model):
    __tablename__ = "report_digital_signatures"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = db.Column(db.String(36), db.ForeignKey("clinical_reports.id"), nullable=False, index=True)
    signer_id = db.Column(db.String(36))
    signer_name = db.Column(db.String(255))
    signer_role = db.Column(db.String(50))
    signed_at = db.Column(db.DateTime)
    signature_hash = db.Column(db.String(128))
    report_hash = db.Column(db.String(128))
    signature_method = db.Column(db.String(50), default="INTERNAL_APPROVAL")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "report_id": self.report_id,
            "signer_id": self.signer_id,
            "signer_name": self.signer_name,
            "signer_role": self.signer_role,
            "signed_at": self.signed_at.isoformat() if self.signed_at else None,
            "signature_hash": self.signature_hash,
            "report_hash": self.report_hash,
            "signature_method": self.signature_method,
        }


class CriticalResultAlert(db.Model):
    __tablename__ = "critical_result_alerts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = db.Column(db.String(50), nullable=False, index=True)
    order_id = db.Column(db.String(36))
    order_code = db.Column(db.String(50))
    result_id = db.Column(db.String(36))
    report_id = db.Column(db.String(36))
    critical_type = db.Column(db.String(50))
    acknowledged_by = db.Column(db.String(255))
    acknowledged_at = db.Column(db.DateTime)
    status = db.Column(db.String(30), default="new", index=True)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "order_code": self.order_code,
            "critical_type": self.critical_type,
            "status": self.status,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "note": self.note,
        }


class ReportNotificationEvent(db.Model):
    __tablename__ = "report_notification_events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = db.Column(db.String(50), nullable=False)
    recipient_type = db.Column(db.String(30))
    recipient_id = db.Column(db.String(50))
    channel = db.Column(db.String(30))
    status = db.Column(db.String(30), default="pending")
    payload_json = db.Column(db.Text)
    report_id = db.Column(db.String(36))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "recipient_type": self.recipient_type,
            "recipient_id": self.recipient_id,
            "channel": self.channel,
            "status": self.status,
            "report_id": self.report_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
