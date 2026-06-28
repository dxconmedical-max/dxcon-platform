from datetime import datetime
import uuid

from app.extensions.db import db


class MedicalOrder(db.Model):

    __tablename__ = "medical_orders"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    order_code = db.Column(db.String(50), unique=True, nullable=False)

    marketplace_booking_id = db.Column(
        db.String(36),
        db.ForeignKey("marketplace_bookings.id"),
        unique=True,
    )

    legacy_order_id = db.Column(
        db.String(36),
        db.ForeignKey("orders.id"),
    )

    patient_id = db.Column(db.String(36))

    patient_name = db.Column(db.String(255), nullable=False)

    patient_phone = db.Column(db.String(30))

    partner_id = db.Column(db.String(36))

    diagnostic_service_id = db.Column(db.String(36))

    collector_id = db.Column(db.String(36))

    status = db.Column(db.String(50), default="BOOKED", nullable=False)

    total_amount = db.Column(db.Float, default=0)

    payment_status = db.Column(db.String(50))

    barcode_value = db.Column(db.String(100), unique=True)

    qr_payload = db.Column(db.String(255))

    note = db.Column(db.Text)

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
            "marketplace_booking_id": self.marketplace_booking_id,
            "legacy_order_id": self.legacy_order_id,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "patient_phone": self.patient_phone,
            "partner_id": self.partner_id,
            "diagnostic_service_id": self.diagnostic_service_id,
            "collector_id": self.collector_id,
            "status": self.status,
            "total_amount": self.total_amount,
            "payment_status": self.payment_status,
            "barcode_value": self.barcode_value,
            "qr_payload": self.qr_payload,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
