from datetime import datetime
import uuid

from app.extensions.db import db


class Organization(db.Model):
    __tablename__ = "crm_organizations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    org_type = db.Column(db.String(50), default="CORPORATE")
    industry = db.Column(db.String(100))
    tax_code = db.Column(db.String(50))
    address = db.Column(db.String(500))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
    owner = db.Column(db.String(255))
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "org_code": self.org_code,
            "name": self.name,
            "org_type": self.org_type,
            "industry": self.industry,
            "tax_code": self.tax_code,
            "address": self.address,
            "phone": self.phone,
            "email": self.email,
            "owner": self.owner,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Customer(db.Model):
    __tablename__ = "crm_customers"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    organization_id = db.Column(db.String(36), db.ForeignKey("crm_organizations.id"))
    customer_type = db.Column(db.String(50), default="B2B")
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    billing_address = db.Column(db.String(500))
    owner = db.Column(db.String(255))
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "customer_code": self.customer_code,
            "name": self.name,
            "organization_id": self.organization_id,
            "customer_type": self.customer_type,
            "email": self.email,
            "phone": self.phone,
            "billing_address": self.billing_address,
            "owner": self.owner,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ContactPerson(db.Model):
    __tablename__ = "crm_contact_persons"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey("crm_organizations.id"))
    customer_id = db.Column(db.String(36), db.ForeignKey("crm_customers.id"))
    full_name = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(100))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "customer_id": self.customer_id,
            "full_name": self.full_name,
            "title": self.title,
            "email": self.email,
            "phone": self.phone,
            "is_primary": self.is_primary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
