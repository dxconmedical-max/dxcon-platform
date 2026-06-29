from datetime import datetime
import uuid

from app.extensions.db import db


class BillingAccount(db.Model):

    __tablename__ = "billing_accounts"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    account_code = db.Column(db.String(50), unique=True, nullable=False)

    owner_type = db.Column(db.String(50), nullable=False)

    owner_id = db.Column(db.String(36), nullable=False)

    currency = db.Column(db.String(10), default="VND")

    balance = db.Column(db.Float, default=0)

    status = db.Column(db.String(20), default="ACTIVE")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "account_code": self.account_code,
            "owner_type": self.owner_type,
            "owner_id": self.owner_id,
            "currency": self.currency,
            "balance": self.balance,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
