from datetime import datetime
import uuid

from app.extensions.db import db


class PaymentRecord(db.Model):

    __tablename__ = "payment_records"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = db.Column(db.String(36), db.ForeignKey("invoices.id"), nullable=False)
    payment_code = db.Column(db.String(50), unique=True, nullable=False)
    amount = db.Column(db.Float, default=0)
    payment_method = db.Column(db.String(50), default="BANK_TRANSFER")
    status = db.Column(db.String(50), default="PENDING")
    transaction_ref = db.Column(db.String(100))
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "payment_code": self.payment_code,
            "amount": self.amount,
            "payment_method": self.payment_method,
            "status": self.status,
            "transaction_ref": self.transaction_ref,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
