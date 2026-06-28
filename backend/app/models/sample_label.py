from datetime import datetime
import uuid

from app.extensions.db import db


class SampleLabel(db.Model):

    __tablename__ = "sample_labels"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    medical_order_id = db.Column(
        db.String(36),
        db.ForeignKey("medical_orders.id"),
        nullable=False,
    )

    sample_id = db.Column(
        db.String(36),
        db.ForeignKey("medical_samples.id"),
        nullable=False,
    )

    label_code = db.Column(db.String(100), unique=True, nullable=False)

    template_name = db.Column(db.String(100), default="STANDARD")

    print_payload = db.Column(db.Text)

    status = db.Column(db.String(50), default="PENDING")

    printed_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "medical_order_id": self.medical_order_id,
            "sample_id": self.sample_id,
            "label_code": self.label_code,
            "template_name": self.template_name,
            "print_payload": self.print_payload,
            "status": self.status,
            "printed_at": self.printed_at.isoformat() if self.printed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
