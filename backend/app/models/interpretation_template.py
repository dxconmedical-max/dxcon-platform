from datetime import datetime
import uuid

from app.extensions.db import db


class InterpretationTemplate(db.Model):

    __tablename__ = "interpretation_templates"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    template_code = db.Column(db.String(50), nullable=False)

    version = db.Column(db.Integer, default=1)

    language = db.Column(db.String(10), default="en")

    title = db.Column(db.String(255))

    body_template = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(20), default="ACTIVE")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("template_code", "version", "language", name="uq_interp_template_version_lang"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "template_code": self.template_code,
            "version": self.version,
            "language": self.language,
            "title": self.title,
            "body_template": self.body_template,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
