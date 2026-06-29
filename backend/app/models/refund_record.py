from datetime import datetime
import uuid

from app.extensions.db import db


class RefundRecord(db.Model):

    __tablename__ = "refund_records"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    refund_code = db.Column(db.String(50), unique=True, nullable=False)
    invoice_id = db.Column(db.String(36), db.ForeignKey("invoices.id"), nullable=False)
    medical_order_id = db.Column(db.String(36), db.ForeignKey("medical_orders.id"))
    payment_record_id = db.Column(db.String(36), db.ForeignKey("payment_records.id"))
    amount = db.Column(db.Float, default=0)
    reason = db.Column(db.Text)
    status = db.Column(db.String(50), default="PENDING")
    processed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "refund_code": self.refund_code,
            "invoice_id": self.invoice_id,
            "medical_order_id": self.medical_order_id,
            "payment_record_id": self.payment_record_id,
            "amount": self.amount,
            "reason": self.reason,
            "status": self.status,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
