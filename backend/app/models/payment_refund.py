from datetime import datetime
import uuid

from app.extensions.db import db


class Refund(db.Model):

    __tablename__ = "payment_refunds"

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

    transaction_id = db.Column(
        db.String(36),
        db.ForeignKey("payment_transactions.id"),
    )

    refund_code = db.Column(db.String(50), unique=True, nullable=False)

    provider = db.Column(db.String(50), nullable=False)

    provider_refund_id = db.Column(db.String(100))

    amount = db.Column(db.Float, default=0)

    reason = db.Column(db.Text)

    status = db.Column(db.String(50), default="PENDING")

    processed_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "payment_id": self.payment_id,
            "transaction_id": self.transaction_id,
            "refund_code": self.refund_code,
            "provider": self.provider,
            "provider_refund_id": self.provider_refund_id,
            "amount": self.amount,
            "reason": self.reason,
            "status": self.status,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
