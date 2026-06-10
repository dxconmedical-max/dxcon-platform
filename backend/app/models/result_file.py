from app.extensions.db import db
from datetime import datetime
import uuid


class ResultFile(db.Model):

    __tablename__ = "result_files"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    order_id = db.Column(
        db.String(36),
        nullable=False
    )

    file_name = db.Column(
        db.String(255)
    )

    file_path = db.Column(
        db.Text
    )

    uploaded_by = db.Column(
        db.String(36)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "file_name": self.file_name,
            "file_path": self.file_path
        }
