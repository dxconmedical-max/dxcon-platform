from datetime import datetime
import uuid

from app.extensions.db import db


class TaxRecord(db.Model):

    __tablename__ = "tax_records"

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

    tax_code = db.Column(db.String(50), default="VAT")

    tax_rate = db.Column(db.Float, default=0.1)

    tax_amount = db.Column(db.Float, default=0)

    status = db.Column(db.String(20), default="APPLIED")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "tax_code": self.tax_code,
            "tax_rate": self.tax_rate,
            "tax_amount": self.tax_amount,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
