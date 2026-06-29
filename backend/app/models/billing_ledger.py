from datetime import datetime
import uuid

from app.extensions.db import db


class BillingLedger(db.Model):

    __tablename__ = "billing_ledgers"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    account_id = db.Column(
        db.String(36),
        db.ForeignKey("billing_accounts.id"),
        nullable=False,
    )

    entry_type = db.Column(db.String(20), nullable=False)

    amount = db.Column(db.Float, default=0)

    reference_type = db.Column(db.String(50))

    reference_id = db.Column(db.String(36))

    description = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    account = db.relationship("BillingAccount")

    def to_dict(self):
        return {
            "id": self.id,
            "account_id": self.account_id,
            "entry_type": self.entry_type,
            "amount": self.amount,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "account": self.account.to_dict() if self.account else None,
        }
