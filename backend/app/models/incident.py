from app.extensions.db import db
from datetime import datetime
import uuid


class Incident(db.Model):

    __tablename__ = "incidents"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    incident_code = db.Column(db.String(50), unique=True, nullable=False)

    incident_type = db.Column(db.String(100), nullable=False)

    severity = db.Column(db.String(30), default="MEDIUM")

    title = db.Column(db.String(255))

    description = db.Column(db.Text)

    related_object_type = db.Column(db.String(100))

    related_object_id = db.Column(db.String(100))

    status = db.Column(db.String(50), default="OPEN")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    resolved_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "incident_code": self.incident_code,
            "incident_type": self.incident_type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "related_object_type": self.related_object_type,
            "related_object_id": self.related_object_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }
