from datetime import datetime
import uuid

from app.extensions.db import db


class BillingAdjustment(db.Model):

    __tablename__ = "billing_adjustments"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    invoice_id = db.Column(
        db.String(36),
        db.ForeignKey("invoices.id"),
        nullable=False,
    )

    adjustment_type = db.Column(db.String(50), nullable=False)

    amount = db.Column(db.Float, default=0)

    reason = db.Column(db.Text)

    status = db.Column(db.String(20), default="PENDING")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "adjustment_type": self.adjustment_type,
            "amount": self.amount,
            "reason": self.reason,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
