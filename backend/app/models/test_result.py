from app.extensions.db import db
from datetime import datetime
import uuid


class TestResult(db.Model):

    __tablename__ = "test_results"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_item_id = db.Column(db.String(36), nullable=False)
    test_name = db.Column(db.String(255))
    result_value = db.Column(db.String(255))
    unit = db.Column(db.String(50))
    reference_range = db.Column(db.String(255))
    flag = db.Column(db.String(20), default="NORMAL")
    interpretation = db.Column(db.Text)
    approval_status = db.Column(db.String(30), default="PENDING")

    approved_by = db.Column(db.String(255))
    approved_at = db.Column(db.String(100))
    doctor_license = db.Column(db.String(100))
    signature_id = db.Column(db.String(100))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "order_item_id": self.order_item_id,
            "test_name": self.test_name,
            "result_value": self.result_value,
            "unit": self.unit,
            "reference_range": self.reference_range,
            "flag": self.flag,
            "interpretation": self.interpretation,
            "approval_status": self.approval_status,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "doctor_license": self.doctor_license,
            "signature_id": self.signature_id
        }
