from app.extensions.db import db
from datetime import datetime
import uuid


class SampleCollection(db.Model):

    __tablename__ = "sample_collections"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    order_id = db.Column(
        db.String(36),
        nullable=False
    )

    collector_name = db.Column(
        db.String(255)
    )

    status = db.Column(
        db.String(50),
        default="PENDING"
    )

    collected_at = db.Column(
        db.DateTime
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "collector_name": self.collector_name,
            "status": self.status,
            "collected_at": str(self.collected_at)
        }
