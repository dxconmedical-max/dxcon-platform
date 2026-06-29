from datetime import datetime
import uuid

from app.extensions.db import db


class CollectorPayout(db.Model):

    __tablename__ = "collector_payouts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payout_code = db.Column(db.String(50), unique=True, nullable=False)
    collector_id = db.Column(db.String(36), db.ForeignKey("drivers.id"), nullable=False)
    settlement_id = db.Column(db.String(36), db.ForeignKey("partner_settlements.id"))
    amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(50), default="PENDING")
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "payout_code": self.payout_code,
            "collector_id": self.collector_id,
            "settlement_id": self.settlement_id,
            "amount": self.amount,
            "status": self.status,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
