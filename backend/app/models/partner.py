from datetime import datetime
import uuid

from app.extensions.db import db


class Partner(db.Model):

    __tablename__ = "partners"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    partner_code = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
    )

    partner_type = db.Column(
        db.String(50),
        nullable=False,
    )

    legal_name = db.Column(
        db.String(255),
        nullable=False,
    )

    display_name = db.Column(
        db.String(255),
        nullable=False,
    )

    tax_code = db.Column(
        db.String(50),
    )

    license_number = db.Column(
        db.String(100),
    )

    representative_name = db.Column(
        db.String(255),
    )

    phone = db.Column(
        db.String(30),
    )

    email = db.Column(
        db.String(255),
    )

    address = db.Column(
        db.Text,
    )

    city = db.Column(
        db.String(100),
    )

    province = db.Column(
        db.String(100),
    )

    district = db.Column(
        db.String(100),
    )

    status = db.Column(
        db.String(50),
        default="DRAFT",
        nullable=False,
    )

    verification_note = db.Column(
        db.Text,
    )

    api_status = db.Column(
        db.String(50),
        default="OFFLINE",
        nullable=False,
    )

    average_result_time_hours = db.Column(
        db.Float,
    )

    pickup_sla_minutes = db.Column(
        db.Integer,
    )

    response_sla_minutes = db.Column(
        db.Integer,
    )

    working_hours_summary = db.Column(
        db.String(500),
    )

    rating = db.Column(
        db.Float,
        default=0.0,
    )

    review_count = db.Column(
        db.Integer,
        default=0,
    )

    completed_orders = db.Column(
        db.Integer,
        default=0,
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

    branches = db.relationship(
        "PartnerBranch",
        backref="partner",
        lazy=True,
        cascade="all, delete-orphan",
    )

    services = db.relationship(
        "PartnerService",
        backref="partner",
        lazy=True,
        cascade="all, delete-orphan",
    )

    documents = db.relationship(
        "PartnerDocument",
        backref="partner",
        lazy=True,
        cascade="all, delete-orphan",
    )

    coverage_areas = db.relationship(
        "PartnerCoverageArea",
        backref="partner",
        lazy=True,
        cascade="all, delete-orphan",
    )

    operating_hours = db.relationship(
        "PartnerOperatingHour",
        backref="partner",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "partner_code": self.partner_code,
            "partner_type": self.partner_type,
            "legal_name": self.legal_name,
            "display_name": self.display_name,
            "tax_code": self.tax_code,
            "license_number": self.license_number,
            "representative_name": self.representative_name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "city": self.city,
            "province": self.province,
            "district": self.district,
            "status": self.status,
            "verification_note": self.verification_note,
            "api_status": self.api_status,
            "average_result_time_hours": self.average_result_time_hours,
            "pickup_sla_minutes": self.pickup_sla_minutes,
            "response_sla_minutes": self.response_sla_minutes,
            "working_hours_summary": self.working_hours_summary,
            "rating": self.rating,
            "review_count": self.review_count,
            "completed_orders": self.completed_orders,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
