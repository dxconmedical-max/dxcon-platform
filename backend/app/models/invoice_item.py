from datetime import datetime
import uuid

from app.extensions.db import db


class InvoiceItem(db.Model):

    __tablename__ = "invoice_items"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = db.Column(db.String(36), db.ForeignKey("invoices.id"), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    service_code = db.Column(db.String(50))
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, default=0)
    line_total = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "description": self.description,
            "service_code": self.service_code,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "line_total": self.line_total,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
