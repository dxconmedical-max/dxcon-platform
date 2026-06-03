from app.extensions.db import db
from datetime import datetime
import uuid


class Company(db.Model):

    __tablename__ = "companies"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    company_code = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    company_name = db.Column(
        db.String(255),
        nullable=False
    )

    tax_code = db.Column(
        db.String(50)
    )

    contact_person = db.Column(
        db.String(255)
    )

    phone = db.Column(
        db.String(30)
    )

    email = db.Column(
        db.String(255)
    )

    address = db.Column(
        db.Text
    )

    status = db.Column(
        db.String(50),
        default="ACTIVE"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "company_code": self.company_code,
            "company_name": self.company_name,
            "tax_code": self.tax_code,
            "contact_person": self.contact_person,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "status": self.status
        }
