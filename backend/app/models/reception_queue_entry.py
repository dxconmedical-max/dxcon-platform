from __future__ import annotations

from datetime import date, datetime
import uuid

from app.extensions.db import db


class ReceptionQueueEntry(db.Model):
    __tablename__ = "reception_queue_entries"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    queue_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    queue_date = db.Column(db.Date, nullable=False, index=True)
    daily_sequence = db.Column(db.Integer, nullable=False)
    patient_id = db.Column(
        db.String(50),
        db.ForeignKey("patients.patient_code"),
        nullable=False,
        index=True,
    )
    visit_type = db.Column(db.String(30), nullable=False, default="WALK_IN")
    status = db.Column(db.String(30), nullable=False, default="WAITING", index=True)
    appointment_id = db.Column(db.String(36))
    payment_status = db.Column(db.String(30), nullable=False, default="PENDING")
    order_id = db.Column(db.String(36), index=True)
    invoice_id = db.Column(db.String(36))
    workflow_status = db.Column(db.String(30), nullable=False, default="WAITING", index=True)
    notes = db.Column(db.Text)
    checked_in_at = db.Column(db.DateTime)
    checked_out_at = db.Column(db.DateTime)
    created_by = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "queue_number": self.queue_number,
            "queue_date": self.queue_date.isoformat() if self.queue_date else None,
            "daily_sequence": self.daily_sequence,
            "patient_id": self.patient_id,
            "visit_type": self.visit_type,
            "status": self.status,
            "appointment_id": self.appointment_id,
            "payment_status": self.payment_status,
            "order_id": self.order_id,
            "invoice_id": self.invoice_id,
            "workflow_status": self.workflow_status,
            "notes": self.notes,
            "checked_in_at": self.checked_in_at.isoformat() if self.checked_in_at else None,
            "checked_out_at": self.checked_out_at.isoformat() if self.checked_out_at else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
