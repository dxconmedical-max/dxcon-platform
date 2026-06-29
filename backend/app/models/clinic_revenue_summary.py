from datetime import datetime
import uuid

from app.extensions.db import db


class ClinicRevenueSummary(db.Model):

    __tablename__ = "clinic_revenue_summaries"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    clinic_id = db.Column(db.String(36), nullable=False, index=True)

    period_start = db.Column(db.DateTime)

    period_end = db.Column(db.DateTime)

    gross_amount = db.Column(db.Float, default=0)

    net_amount = db.Column(db.Float, default=0)

    orders_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "clinic_id": self.clinic_id,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "gross_amount": self.gross_amount,
            "net_amount": self.net_amount,
            "orders_count": self.orders_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
