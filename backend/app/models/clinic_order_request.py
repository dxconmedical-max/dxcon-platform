import json
from datetime import datetime
import uuid

from app.extensions.db import db


class ClinicOrderRequest(db.Model):
    """A simple test request (phiếu chỉ định) submitted by a clinic; DxCon staff approve it into a real order."""

    __tablename__ = "clinic_order_requests"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference = db.Column(db.String(24), unique=True, nullable=False)
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    requested_by = db.Column(db.String(120))
    patient_name = db.Column(db.String(120), nullable=False)
    birth_year = db.Column(db.Integer, nullable=False)
    tests_json = db.Column(db.Text, nullable=False)  # [{"id","code","name"}]
    tube_count = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(20), nullable=False, default="NEW", index=True)  # NEW / APPROVED / REJECTED
    order_code = db.Column(db.String(50))
    reject_reason = db.Column(db.String(300))
    handled_by = db.Column(db.String(120))
    handled_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    @property
    def tests(self) -> list[dict]:
        try:
            return json.loads(self.tests_json or "[]")
        except ValueError:
            return []

    def to_dict(self, *, organization_name: str | None = None) -> dict:
        return {
            "id": self.id,
            "reference": self.reference,
            "organization_id": self.organization_id,
            "organization_name": organization_name,
            "requested_by": self.requested_by,
            "patient_name": self.patient_name,
            "birth_year": self.birth_year,
            "tests": self.tests,
            "tube_count": self.tube_count,
            "status": self.status,
            "order_code": self.order_code,
            "reject_reason": self.reject_reason,
            "handled_by": self.handled_by,
            "handled_at": self.handled_at.isoformat() if self.handled_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ClinicOrderSetting(db.Model):
    """Per-clinic switch: may this clinic submit its own requests? Off unless DxCon turns it on."""

    __tablename__ = "clinic_order_settings"

    organization_id = db.Column(db.String(36), primary_key=True)
    enabled = db.Column(db.Boolean, nullable=False, default=False)
    updated_by = db.Column(db.String(120))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
