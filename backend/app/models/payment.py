from app.extensions.db import db
from datetime import datetime
import uuid


class Payment(db.Model):

    __tablename__ = "payments"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    invoice_id = db.Column(
        db.String(36),
        nullable=False
    )

    amount = db.Column(
        db.Float,
        default=0
    )

    payment_method = db.Column(
        db.String(50),
        default="BANK_TRANSFER"
    )

    payment_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    status = db.Column(
        db.String(50),
        default="PAID"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "amount": self.amount,
            "payment_method": self.payment_method,
            "status": self.status,
            "payment_date": str(self.payment_date)
        }
