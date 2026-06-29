from datetime import datetime
import uuid

from app.extensions.db import db


class ResultAttachment(db.Model):

    __tablename__ = "result_attachments"

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

    file_name = db.Column(db.String(255), nullable=False)

    file_path = db.Column(db.Text, nullable=False)

    mime_type = db.Column(db.String(100))

    attachment_type = db.Column(db.String(20), default="PDF")

    uploaded_by = db.Column(db.String(255), default="SYSTEM")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "lab_result_id": self.lab_result_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "mime_type": self.mime_type,
            "attachment_type": self.attachment_type,
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
