"""Sprint 005 — Multi-tenant organization and partner foundation models."""

from __future__ import annotations

from datetime import datetime
import json
import uuid

from app.extensions.db import db

ORG_STATUS_ACTIVE = "active"
ORG_STATUS_INACTIVE = "inactive"
ORG_STATUS_SUSPENDED = "suspended"

ORGANIZATION_TYPES: tuple[str, ...] = (
    "DXCON_INTERNAL",
    "CLINIC",
    "HOSPITAL",
    "LABORATORY",
    "CORPORATE",
    "INSURANCE",
    "PARTNER",
)

ORG_ROLES: tuple[str, ...] = (
    "ORG_OWNER",
    "CLINIC_ADMIN",
    "DOCTOR",
    "RECEPTION",
    "COLLECTOR",
    "FINANCE",
    "VIEWER",
)

PERMISSION_ACTIONS: tuple[str, ...] = (
    "view",
    "create",
    "update",
    "delete",
    "approve",
    "export",
    "import",
)


class PartnerOrganization(db.Model):
    """Canonical organization for Sprint 005 multi-tenant platform."""

    __tablename__ = "organizations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    organization_name = db.Column(db.String(255), nullable=False)
    organization_type = db.Column(db.String(50), nullable=False, default="CLINIC")
    tax_code = db.Column(db.String(50))
    business_license = db.Column(db.String(100))
    address = db.Column(db.String(500))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
    website = db.Column(db.String(255))
    contact_person = db.Column(db.String(255))
    status = db.Column(db.String(30), default=ORG_STATUS_ACTIVE, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization_code": self.organization_code,
            "organization_name": self.organization_name,
            "organization_type": self.organization_type,
            "tax_code": self.tax_code,
            "business_license": self.business_license,
            "address": self.address,
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
            "contact_person": self.contact_person,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class OrganizationUser(db.Model):
    """Organization membership — user belongs to one organization with org role."""

    __tablename__ = "organization_users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    role_code = db.Column(db.String(50), nullable=False, default="VIEWER")
    active = db.Column(db.Boolean, default=True, nullable=False)
    invited_by = db.Column(db.String(255))
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("organization_id", "user_id", name="uq_org_user"),)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "role_code": self.role_code,
            "active": self.active,
            "invited_by": self.invited_by,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class OrganizationRole(db.Model):
    """Organization-scoped role definition with permission matrix."""

    __tablename__ = "organization_roles"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role_code = db.Column(db.String(50), unique=True, nullable=False)
    role_name = db.Column(db.String(100), nullable=False)
    permissions_json = db.Column(db.Text, default="[]")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def permissions(self) -> list[str]:
        try:
            return json.loads(self.permissions_json or "[]")
        except json.JSONDecodeError:
            return []

    def set_permissions(self, perms: list[str]) -> None:
        self.permissions_json = json.dumps(perms)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role_code": self.role_code,
            "role_name": self.role_name,
            "permissions": self.permissions(),
            "is_active": self.is_active,
        }


class PartnerContract(db.Model):
    """Partner contract linked to organization."""

    __tablename__ = "partner_contracts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    organization_id = db.Column(db.String(36), db.ForeignKey("organizations.id"), nullable=False, index=True)
    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))
    discount_percent = db.Column(db.Float, default=0)
    payment_terms = db.Column(db.String(100))
    status = db.Column(db.String(30), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "contract_code": self.contract_code,
            "organization_id": self.organization_id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "discount_percent": self.discount_percent,
            "payment_terms": self.payment_terms,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class OrganizationPriceList(db.Model):
    """Organization-specific price list assignment with tier and fallback."""

    __tablename__ = "organization_price_lists"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey("organizations.id"), nullable=False, index=True)
    price_list_code = db.Column(db.String(100), nullable=False)
    price_tier = db.Column(db.String(30), nullable=False, default="retail")
    effective_from = db.Column(db.String(20))
    effective_to = db.Column(db.String(20))
    is_default = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(30), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("organization_id", "price_tier", name="uq_org_price_tier"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "price_list_code": self.price_list_code,
            "price_tier": self.price_tier,
            "effective_from": self.effective_from,
            "effective_to": self.effective_to,
            "is_default": self.is_default,
            "status": self.status,
        }
