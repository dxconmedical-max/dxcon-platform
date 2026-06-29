from datetime import datetime
import uuid

from app.extensions.db import db


class CommissionRule(db.Model):

    __tablename__ = "commission_rules"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_code = db.Column(db.String(50), unique=True, nullable=False)
    partner_type = db.Column(db.String(50))
    partner_id = db.Column(db.String(36), db.ForeignKey("partners.id"))
    role_type = db.Column(db.String(50), default="PARTNER")
    rate_percent = db.Column(db.Float, default=0)
    flat_fee = db.Column(db.Float, default=0)
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "rule_code": self.rule_code,
            "partner_type": self.partner_type,
            "partner_id": self.partner_id,
            "role_type": self.role_type,
            "rate_percent": self.rate_percent,
            "flat_fee": self.flat_fee,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
