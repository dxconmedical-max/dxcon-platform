from app.extensions.db import db
from datetime import datetime
import uuid


class DispatchItem(db.Model):

    __tablename__ = "dispatch_items"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    dispatch_job_id = db.Column(db.String(36), nullable=False)

    sample_tracking_id = db.Column(db.String(36), nullable=False)

    sequence_no = db.Column(db.Integer, default=1)

    status = db.Column(db.String(50), default="ASSIGNED")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "dispatch_job_id": self.dispatch_job_id,
            "sample_tracking_id": self.sample_tracking_id,
            "sequence_no": self.sequence_no,
            "status": self.status,
        }
