from datetime import datetime
import uuid

from app.extensions.db import db


class ResultRelease(db.Model):

    __tablename__ = "result_releases"

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

    release_code = db.Column(db.String(50), unique=True, nullable=False)

    released_by = db.Column(db.String(255), default="SYSTEM")

    release_channel = db.Column(db.String(50), default="PORTAL")

    payload_json = db.Column(db.Text, nullable=False)

    version = db.Column(db.Integer, default=1)

    released_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "lab_result_id": self.lab_result_id,
            "release_code": self.release_code,
            "released_by": self.released_by,
            "release_channel": self.release_channel,
            "payload_json": self.payload_json,
            "version": self.version,
            "released_at": self.released_at.isoformat() if self.released_at else None,
        }
