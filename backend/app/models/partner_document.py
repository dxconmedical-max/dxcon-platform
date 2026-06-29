from datetime import datetime
import uuid

from app.extensions.db import db


class PartnerDocument(db.Model):

    __tablename__ = "partner_documents"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    partner_id = db.Column(
        db.String(36),
        db.ForeignKey("partners.id"),
        nullable=False,
    )

    document_type = db.Column(
        db.String(50),
        nullable=False,
    )

    document_name = db.Column(
        db.String(255),
        nullable=False,
    )

    file_reference = db.Column(
        db.String(500),
    )

    status = db.Column(
        db.String(50),
        default="PENDING",
    )

    uploaded_at = db.Column(
        db.DateTime,
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "partner_id": self.partner_id,
            "document_type": self.document_type,
            "document_name": self.document_name,
            "file_reference": self.file_reference,
            "status": self.status,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
