from datetime import datetime
import uuid

from app.extensions.db import db


class PaymentTransaction(db.Model):

    __tablename__ = "payment_transactions"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    payment_id = db.Column(
        db.String(36),
        db.ForeignKey("payments.id"),
        nullable=False,
    )

    provider = db.Column(db.String(50), nullable=False)

    external_transaction_id = db.Column(db.String(100), unique=True, nullable=False)

    amount = db.Column(db.Float, default=0)

    currency = db.Column(db.String(10), default="VND")

    status = db.Column(db.String(50), default="PENDING")

    raw_response_json = db.Column(db.Text, default="{}")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    payment = db.relationship("Payment")

    def to_dict(self):
        return {
            "id": self.id,
            "payment_id": self.payment_id,
            "provider": self.provider,
            "external_transaction_id": self.external_transaction_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "raw_response_json": self.raw_response_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
