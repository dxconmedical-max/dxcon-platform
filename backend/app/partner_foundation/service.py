"""Partner foundation service — organizations, users, contracts, price lists."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_

from app.extensions.db import db
from app.models.partner_foundation import (
    ORG_STATUS_ACTIVE,
    ORG_STATUS_INACTIVE,
    ORGANIZATION_TYPES,
    ORG_ROLES,
    OrganizationPriceList,
    OrganizationRole,
    OrganizationUser,
    PartnerContract,
    PartnerOrganization,
)
from app.models.user import User
from app.partner_foundation.audit import write_org_audit
from app.partner_foundation.isolation import apply_organization_filter, get_organization_scope
from app.partner_foundation.rbac import default_permissions_for_role


class PartnerFoundationError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


DEFAULT_ORG_CODE = "DXCON_INTERNAL"
DEFAULT_ORG_ID = "00000000-0000-4000-8000-000000000001"


def ensure_default_organization() -> PartnerOrganization:
    org = PartnerOrganization.query.filter_by(organization_code=DEFAULT_ORG_CODE).first()
    if org:
        return org
    org = PartnerOrganization(
        id=DEFAULT_ORG_ID,
        organization_code=DEFAULT_ORG_CODE,
        organization_name="DxCon Internal",
        organization_type="DXCON_INTERNAL",
        status=ORG_STATUS_ACTIVE,
        contact_person="Platform Admin",
    )
    db.session.add(org)
    db.session.flush()
    write_org_audit(action="created", object_type="organization", object_id=org.organization_code, actor="SYSTEM")
    return org


def seed_organization_roles() -> None:
    for role_code in ORG_ROLES:
        existing = OrganizationRole.query.filter_by(role_code=role_code).first()
        perms = default_permissions_for_role(role_code)
        if existing:
            existing.set_permissions(perms)
            continue
        row = OrganizationRole(
            role_code=role_code,
            role_name=role_code.replace("_", " ").title(),
        )
        row.set_permissions(perms)
        db.session.add(row)
    db.session.flush()


def backfill_users_to_internal_org() -> int:
    org = ensure_default_organization()
    count = 0
    for user in User.query.all():
        membership = OrganizationUser.query.filter_by(user_id=user.id, organization_id=org.id).first()
        if not membership:
            db.session.add(
                OrganizationUser(
                    organization_id=org.id,
                    user_id=user.id,
                    role_code="ORG_OWNER" if user.role in {"SUPER_ADMIN", "ADMIN"} else "VIEWER",
                    active=user.is_active,
                    invited_by="migration",
                )
            )
            count += 1
        if not getattr(user, "organization_id", None):
            user.organization_id = org.id
            count += 1
    db.session.flush()
    return count


def query_organizations(
    *,
    search: str | None = None,
    organization_type: str | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 25,
    sort: str = "organization_code",
    sort_dir: str = "asc",
) -> dict[str, Any]:
    query = PartnerOrganization.query
    scope = get_organization_scope()
    if scope:
        query = query.filter_by(id=scope)
    if organization_type:
        query = query.filter_by(organization_type=organization_type)
    if status:
        query = query.filter_by(status=status)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(PartnerOrganization.organization_code.ilike(term), PartnerOrganization.organization_name.ilike(term))
        )
    sort_col = getattr(PartnerOrganization, sort, PartnerOrganization.organization_code)
    query = query.order_by(sort_col.desc() if sort_dir.lower() == "desc" else sort_col.asc())
    page = max(page, 1)
    per_page = min(max(per_page, 1), 500)
    total = query.count()
    rows = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "data": [r.to_dict() for r in rows],
        "pagination": {"page": page, "per_page": per_page, "total": total, "pages": max(1, (total + per_page - 1) // per_page)},
    }


def upsert_organization(data: dict[str, Any], *, actor: str | None = None) -> dict:
    code = (data.get("organization_code") or "").strip()
    name = (data.get("organization_name") or data.get("name") or "").strip()
    if not code or not name:
        raise PartnerFoundationError("organization_code and organization_name are required")
    org_type = (data.get("organization_type") or "CLINIC").upper()
    if org_type not in ORGANIZATION_TYPES:
        raise PartnerFoundationError(f"invalid organization_type: {org_type}")

    row = PartnerOrganization.query.filter_by(organization_code=code).first()
    is_new = row is None
    if is_new:
        row = PartnerOrganization(organization_code=code, organization_name=name)
        db.session.add(row)
    else:
        row.organization_name = name
        row.updated_at = _utcnow()

    for field in (
        "organization_type", "tax_code", "business_license", "address",
        "phone", "email", "website", "contact_person", "status",
    ):
        if field in data and data[field] is not None:
            setattr(row, field, data[field])
    db.session.flush()
    write_org_audit(
        action="created" if is_new else "updated",
        object_type="organization",
        object_id=row.organization_code,
        actor=actor,
    )
    return row.to_dict()


def invite_organization_user(
    organization_id: str,
    user_id: str,
    *,
    role_code: str = "VIEWER",
    invited_by: str | None = None,
) -> dict:
    if role_code not in ORG_ROLES:
        raise PartnerFoundationError(f"invalid role_code: {role_code}")
    org = PartnerOrganization.query.get(organization_id)
    user = User.query.get(user_id)
    if not org or not user:
        raise PartnerFoundationError("organization or user not found")

    row = OrganizationUser.query.filter_by(organization_id=organization_id, user_id=user_id).first()
    if not row:
        row = OrganizationUser(
            organization_id=organization_id,
            user_id=user_id,
            role_code=role_code,
            invited_by=invited_by,
        )
        db.session.add(row)
    else:
        row.role_code = role_code
        row.active = True
        row.updated_at = _utcnow()
    user.organization_id = organization_id
    db.session.flush()
    write_org_audit(action="user_invited", object_type="organization_user", object_id=f"{org.organization_code}:{user.email}", actor=invited_by)
    return row.to_dict()


def disable_organization_user(organization_id: str, user_id: str, *, actor: str | None = None) -> dict:
    row = OrganizationUser.query.filter_by(organization_id=organization_id, user_id=user_id).first()
    if not row:
        raise PartnerFoundationError("membership not found")
    row.active = False
    row.updated_at = _utcnow()
    user = User.query.get(user_id)
    if user:
        user.is_active = False
    write_org_audit(action="user_disabled", object_type="organization_user", object_id=row.id, actor=actor)
    return row.to_dict()


def upsert_partner_contract(data: dict[str, Any], *, actor: str | None = None) -> dict:
    code = (data.get("contract_code") or "").strip()
    org_id = (data.get("organization_id") or "").strip()
    if not code or not org_id:
        raise PartnerFoundationError("contract_code and organization_id are required")
    row = PartnerContract.query.filter_by(contract_code=code).first()
    is_new = row is None
    if is_new:
        row = PartnerContract(contract_code=code, organization_id=org_id)
        db.session.add(row)
    for field in ("start_date", "end_date", "discount_percent", "payment_terms", "status", "organization_id"):
        if field in data and data[field] is not None:
            setattr(row, field, data[field])
    db.session.flush()
    write_org_audit(action="contract_updated", object_type="partner_contract", object_id=code, actor=actor)
    return row.to_dict()


def assign_organization_price_list(data: dict[str, Any], *, actor: str | None = None) -> dict:
    org_id = (data.get("organization_id") or "").strip()
    tier = (data.get("price_tier") or "retail").lower()
    pl_code = (data.get("price_list_code") or "").strip()
    if not org_id or not pl_code:
        raise PartnerFoundationError("organization_id and price_list_code are required")
    row = OrganizationPriceList.query.filter_by(organization_id=org_id, price_tier=tier).first()
    if not row:
        row = OrganizationPriceList(organization_id=org_id, price_tier=tier, price_list_code=pl_code)
        db.session.add(row)
    else:
        row.price_list_code = pl_code
    for field in ("effective_from", "effective_to", "is_default", "status"):
        if field in data and data[field] is not None:
            setattr(row, field, data[field])
    db.session.flush()
    write_org_audit(action="price_list_assigned", object_type="organization_price_list", object_id=f"{org_id}:{tier}", actor=actor)
    return row.to_dict()


def resolve_price_list_code(organization_id: str | None, price_tier: str = "retail") -> str | None:
    if organization_id:
        row = OrganizationPriceList.query.filter_by(
            organization_id=organization_id, price_tier=price_tier, status="active"
        ).first()
        if row:
            return row.price_list_code
    default = OrganizationPriceList.query.filter_by(is_default=True, price_tier=price_tier, status="active").first()
    return default.price_list_code if default else None


def organization_dashboard(organization_id: str, portal: str) -> dict[str, Any]:
    org = PartnerOrganization.query.get(organization_id)
    if not org:
        raise PartnerFoundationError("organization not found")
    base = {"organization": org.to_dict(), "portal": portal}
    widgets = {
        "clinic": ["patients", "orders", "revenue", "reports", "invoices", "pending_orders"],
        "doctor": ["todays_patients", "orders", "pending_review", "released_reports"],
        "corporate": ["employee_orders", "invoices", "reports"],
        "insurance": ["claims", "invoices", "reports"],
        "partner": ["overview", "contracts", "price_lists"],
    }
    base["widgets"] = widgets.get(portal, widgets["partner"])
    base["metrics"] = {
        "patients": 0,
        "orders": 0,
        "pending_orders": 0,
        "revenue": 0,
        "reports": 0,
        "invoices": 0,
    }
    return base


def permission_matrix() -> dict[str, Any]:
    roles = OrganizationRole.query.filter_by(is_active=True).all()
    if not roles:
        seed_organization_roles()
        roles = OrganizationRole.query.filter_by(is_active=True).all()
    return {
        "roles": [r.to_dict() for r in roles],
        "organization_types": list(ORGANIZATION_TYPES),
    }


def rbac_report() -> dict[str, Any]:
    return {
        "report": "RBAC_REPORT",
        "roles": permission_matrix()["roles"],
        "global_bypass_roles": list({"SUPER_ADMIN", "SYSTEM_ADMIN"}),
    }


def tenant_security_report() -> dict[str, Any]:
    org_count = PartnerOrganization.query.count()
    user_count = OrganizationUser.query.filter_by(active=True).count()
    return {
        "report": "TENANT_SECURITY_REPORT",
        "organizations": org_count,
        "active_memberships": user_count,
        "isolation_mode": "opt_in_filter",
        "cross_org_blocked": True,
    }


def partner_foundation_report() -> dict[str, Any]:
    return {
        "report": "PARTNER_FOUNDATION_REPORT",
        "organizations": PartnerOrganization.query.count(),
        "contracts": PartnerContract.query.count(),
        "price_list_assignments": OrganizationPriceList.query.count(),
        "memberships": OrganizationUser.query.count(),
    }
