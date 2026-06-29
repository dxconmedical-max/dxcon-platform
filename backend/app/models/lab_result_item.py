from datetime import datetime
import uuid

from app.extensions.db import db


class LabResultItem(db.Model):

    __tablename__ = "lab_result_items"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    lab_result_id = db.Column(
        db.String(36),
        db.ForeignKey("lab_results.id"),
        nullable=False,
    )

    test_code = db.Column(db.String(50))

    test_name = db.Column(db.String(255), nullable=False)

    result_value = db.Column(db.String(255))

    unit = db.Column(db.String(50))

    reference_range = db.Column(db.String(255))

    flag = db.Column(db.String(20), default="NORMAL")

    sequence = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "lab_result_id": self.lab_result_id,
            "test_code": self.test_code,
            "test_name": self.test_name,
            "result_value": self.result_value,
            "unit": self.unit,
            "reference_range": self.reference_range,
            "flag": self.flag,
            "sequence": self.sequence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
