import uuid
from datetime import datetime

from app.extensions.db import db


class StaffProfile(db.Model):
    """Display profile (name, title, license) for a staff user, used on report signatures."""

    __tablename__ = "staff_profiles"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, unique=True, index=True)
    full_name = db.Column(db.String(255), nullable=False)
    job_title = db.Column(db.String(255))
    license_number = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
