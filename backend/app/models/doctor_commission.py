from datetime import datetime
import uuid

from app.extensions.db import db


class DoctorCommission(db.Model):

    __tablename__ = "doctor_commissions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    commission_code = db.Column(db.String(50), unique=True, nullable=False)
    doctor_id = db.Column(db.String(36))
    medical_order_id = db.Column(db.String(36), db.ForeignKey("medical_orders.id"))
    invoice_id = db.Column(db.String(36), db.ForeignKey("invoices.id"))
    amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(50), default="PENDING")
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "commission_code": self.commission_code,
            "doctor_id": self.doctor_id,
            "medical_order_id": self.medical_order_id,
            "invoice_id": self.invoice_id,
            "amount": self.amount,
            "status": self.status,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
