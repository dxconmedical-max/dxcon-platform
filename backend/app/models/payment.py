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

    provider = db.Column(db.String(50))

    external_transaction_id = db.Column(db.String(100))

    payment_method_id = db.Column(db.String(36))

    metadata_json = db.Column(db.Text, default="{}")

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "amount": self.amount,
            "payment_method": self.payment_method,
            "status": self.status,
            "provider": self.provider,
            "external_transaction_id": self.external_transaction_id,
            "payment_method_id": self.payment_method_id,
            "metadata_json": self.metadata_json,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
