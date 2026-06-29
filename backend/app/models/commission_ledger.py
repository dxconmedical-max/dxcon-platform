from datetime import datetime
import uuid

from app.extensions.db import db


class CommissionLedger(db.Model):

    __tablename__ = "commission_ledger"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ledger_code = db.Column(db.String(50), unique=True, nullable=False)
    medical_order_id = db.Column(db.String(36), db.ForeignKey("medical_orders.id"))
    invoice_id = db.Column(db.String(36), db.ForeignKey("invoices.id"))
    partner_id = db.Column(db.String(36), db.ForeignKey("partners.id"))
    collector_id = db.Column(db.String(36))
    doctor_id = db.Column(db.String(36))
    role_type = db.Column(db.String(50), nullable=False)
    gross_amount = db.Column(db.Float, default=0)
    commission_amount = db.Column(db.Float, default=0)
    rule_id = db.Column(db.String(36), db.ForeignKey("commission_rules.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "ledger_code": self.ledger_code,
            "medical_order_id": self.medical_order_id,
            "invoice_id": self.invoice_id,
            "partner_id": self.partner_id,
            "collector_id": self.collector_id,
            "doctor_id": self.doctor_id,
            "role_type": self.role_type,
            "gross_amount": self.gross_amount,
            "commission_amount": self.commission_amount,
            "rule_id": self.rule_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
