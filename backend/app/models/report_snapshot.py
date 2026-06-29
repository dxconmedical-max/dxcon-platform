from datetime import datetime
import uuid

from app.extensions.db import db


class ReportSnapshot(db.Model):

    __tablename__ = "report_snapshots"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    snapshot_code = db.Column(db.String(50), unique=True, nullable=False)

    report_type = db.Column(db.String(50), nullable=False)

    period_start = db.Column(db.DateTime)

    period_end = db.Column(db.DateTime)

    payload_json = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "snapshot_code": self.snapshot_code,
            "report_type": self.report_type,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "payload_json": self.payload_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
