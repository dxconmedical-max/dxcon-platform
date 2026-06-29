from datetime import datetime
import uuid

from app.extensions.db import db


class ReferenceRange(db.Model):

    __tablename__ = "reference_ranges"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    test_code = db.Column(db.String(50), nullable=False)

    test_name = db.Column(db.String(255))

    sex = db.Column(db.String(10), default="ALL")

    age_min = db.Column(db.Integer, default=0)

    age_max = db.Column(db.Integer, default=120)

    unit = db.Column(db.String(50))

    low_value = db.Column(db.Float)

    high_value = db.Column(db.Float)

    status = db.Column(db.String(20), default="ACTIVE")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "test_code": self.test_code,
            "test_name": self.test_name,
            "sex": self.sex,
            "age_min": self.age_min,
            "age_max": self.age_max,
            "unit": self.unit,
            "low_value": self.low_value,
            "high_value": self.high_value,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def as_range_text(self):
        if self.low_value is not None and self.high_value is not None:
            return f"{self.low_value}-{self.high_value}"
        if self.high_value is not None:
            return f"<{self.high_value}"
        if self.low_value is not None:
            return f">{self.low_value}"
        return ""
