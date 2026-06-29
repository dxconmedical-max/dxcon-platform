from datetime import datetime
import uuid

from app.extensions.db import db


class ClinicOrder(db.Model):

    __tablename__ = "clinic_orders"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    order_code = db.Column(db.String(50), unique=True, nullable=False)

    clinic_id = db.Column(db.String(36), nullable=False)

    patient_id = db.Column(
        db.String(36),
        db.ForeignKey("patients.id"),
        nullable=False,
    )

    medical_order_id = db.Column(db.String(36))

    total_amount = db.Column(db.Float, default=0)

    status = db.Column(db.String(50), default="PENDING")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "order_code": self.order_code,
            "clinic_id": self.clinic_id,
            "patient_id": self.patient_id,
            "medical_order_id": self.medical_order_id,
            "total_amount": self.total_amount,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
