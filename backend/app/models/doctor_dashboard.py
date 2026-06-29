from datetime import datetime
import json
import uuid

from app.extensions.db import db


class DoctorDashboard(db.Model):

    __tablename__ = "doctor_dashboards"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    doctor_id = db.Column(db.String(36), nullable=False, index=True)

    patients_total = db.Column(db.Integer, default=0)

    referrals_total = db.Column(db.Integer, default=0)

    follow_ups_pending = db.Column(db.Integer, default=0)

    notes_total = db.Column(db.Integer, default=0)

    released_results_total = db.Column(db.Integer, default=0)

    schedule_slots = db.Column(db.Integer, default=0)

    snapshot_json = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        payload = {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "patients_total": self.patients_total,
            "referrals_total": self.referrals_total,
            "follow_ups_pending": self.follow_ups_pending,
            "notes_total": self.notes_total,
            "released_results_total": self.released_results_total,
            "schedule_slots": self.schedule_slots,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if self.snapshot_json:
            try:
                payload["snapshot"] = json.loads(self.snapshot_json)
            except (TypeError, json.JSONDecodeError):
                payload["snapshot"] = None
        return payload
