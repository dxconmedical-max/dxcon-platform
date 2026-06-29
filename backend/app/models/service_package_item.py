from datetime import datetime
import uuid

from app.extensions.db import db


class ServicePackageItem(db.Model):

    __tablename__ = "service_package_items"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    package_id = db.Column(
        db.String(36),
        db.ForeignKey("service_packages.id"),
        nullable=False,
    )

    diagnostic_service_id = db.Column(
        db.String(36),
        db.ForeignKey("diagnostic_services.id"),
        nullable=False,
    )

    quantity = db.Column(
        db.Integer,
        default=1,
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )

    service = db.relationship(
        "DiagnosticService",
        backref=db.backref("package_items", lazy=True),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "package_id": self.package_id,
            "diagnostic_service_id": self.diagnostic_service_id,
            "quantity": self.quantity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
