from datetime import datetime
import uuid

from app.extensions.db import db


class ServicePackage(db.Model):

    __tablename__ = "service_packages"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    package_code = db.Column(
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

    target_condition = db.Column(
        db.String(255),
    )

    base_price = db.Column(
        db.Float,
        default=0,
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

    items = db.relationship(
        "ServicePackageItem",
        backref="package",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "package_code": self.package_code,
            "name": self.name,
            "description": self.description,
            "target_condition": self.target_condition,
            "base_price": self.base_price,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
