from datetime import datetime
import uuid

from app.extensions.db import db


class KPIEvent(db.Model):

    __tablename__ = "kpi_events"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    event_code = db.Column(db.String(50), unique=True, nullable=False)

    kpi_code = db.Column(db.String(50), nullable=False)

    kpi_value = db.Column(db.Float, default=0)

    dimension = db.Column(db.String(50))

    reference_id = db.Column(db.String(36))

    metadata_json = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "event_code": self.event_code,
            "kpi_code": self.kpi_code,
            "kpi_value": self.kpi_value,
            "dimension": self.dimension,
            "reference_id": self.reference_id,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
