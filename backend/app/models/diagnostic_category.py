from datetime import datetime
import uuid

from app.extensions.db import db


class DiagnosticCategory(db.Model):

    __tablename__ = "diagnostic_categories"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    category_code = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
    )

    name = db.Column(
        db.String(255),
        nullable=False,
    )

    description = db.Column(
        db.Text,
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

    services = db.relationship(
        "DiagnosticService",
        backref="category",
        lazy=True,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "category_code": self.category_code,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
