from datetime import datetime
import uuid

from app.extensions.db import db


class PartnerSettlement(db.Model):

    __tablename__ = "partner_settlements"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    settlement_code = db.Column(db.String(50), unique=True, nullable=False)
    partner_id = db.Column(db.String(36), db.ForeignKey("partners.id"), nullable=False)
    period_start = db.Column(db.String(20))
    period_end = db.Column(db.String(20))
    gross_amount = db.Column(db.Float, default=0)
    commission_amount = db.Column(db.Float, default=0)
    net_amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(50), default="DRAFT")
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "settlement_code": self.settlement_code,
            "partner_id": self.partner_id,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "gross_amount": self.gross_amount,
            "commission_amount": self.commission_amount,
            "net_amount": self.net_amount,
            "status": self.status,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
