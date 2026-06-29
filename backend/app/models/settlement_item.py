from datetime import datetime
import uuid

from app.extensions.db import db


class SettlementItem(db.Model):

    __tablename__ = "settlement_items"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    settlement_id = db.Column(db.String(36), db.ForeignKey("partner_settlements.id"), nullable=False)
    invoice_id = db.Column(db.String(36), db.ForeignKey("invoices.id"))
    medical_order_id = db.Column(db.String(36), db.ForeignKey("medical_orders.id"))
    description = db.Column(db.String(255))
    gross_amount = db.Column(db.Float, default=0)
    commission_amount = db.Column(db.Float, default=0)
    net_amount = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "settlement_id": self.settlement_id,
            "invoice_id": self.invoice_id,
            "medical_order_id": self.medical_order_id,
            "description": self.description,
            "gross_amount": self.gross_amount,
            "commission_amount": self.commission_amount,
            "net_amount": self.net_amount,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
