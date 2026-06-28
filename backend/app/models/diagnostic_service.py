from datetime import datetime
import uuid

from app.extensions.db import db


class DiagnosticService(db.Model):

    __tablename__ = "diagnostic_services"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    service_code = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
    )

    name = db.Column(
        db.String(255),
        nullable=False,
    )

    short_name = db.Column(
        db.String(100),
    )

    category_id = db.Column(
        db.String(36),
        db.ForeignKey("diagnostic_categories.id"),
        nullable=False,
    )

    sample_type = db.Column(
        db.String(100),
    )

    preparation_instruction = db.Column(
        db.Text,
    )

    fasting_required = db.Column(
        db.Boolean,
        default=False,
    )

    estimated_turnaround_hours = db.Column(
        db.Float,
    )

    home_collection_allowed = db.Column(
        db.Boolean,
        default=False,
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "service_code": self.service_code,
            "name": self.name,
            "short_name": self.short_name,
            "category_id": self.category_id,
            "sample_type": self.sample_type,
            "preparation_instruction": self.preparation_instruction,
            "fasting_required": self.fasting_required,
            "estimated_turnaround_hours": self.estimated_turnaround_hours,
            "home_collection_allowed": self.home_collection_allowed,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
