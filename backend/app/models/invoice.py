from app.extensions.db import db
from datetime import datetime
import uuid


class Invoice(db.Model):

    __tablename__ = "invoices"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    invoice_no = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    company_id = db.Column(
        db.String(36),
        nullable=False
    )

    order_id = db.Column(
        db.String(36),
        nullable=False
    )

    total_amount = db.Column(
        db.Float,
        default=0
    )

    payment_status = db.Column(
        db.String(50),
        default="UNPAID"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_no": self.invoice_no,
            "company_id": self.company_id,
            "order_id": self.order_id,
            "total_amount": self.total_amount,
            "payment_status": self.payment_status
        }
