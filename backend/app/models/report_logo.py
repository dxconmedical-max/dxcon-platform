import uuid
from datetime import datetime

from app.extensions.db import db


class ReportLogo(db.Model):
    """Logo shown on reports. owner_type: DXCON | LABORATORY | PARTNER | CLIENT."""

    __tablename__ = "report_logos"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_type = db.Column(db.String(30), nullable=False)
    owner_code = db.Column(db.String(100), nullable=False, default="")
    display_name = db.Column(db.String(255), nullable=False)
    storage_key = db.Column(db.String(500), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (db.Index("ix_report_logos_owner", "owner_type", "owner_code"),)
