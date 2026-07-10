"""Authenticated user context — memberships, organization switch, capabilities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.permissions import get_role_permissions, role_has_permission
from app.extensions.db import db
from app.models.partner_foundation import (
    ORG_STATUS_ACTIVE,
    ORG_STATUS_SUSPENDED,
    OrganizationUser,
    PartnerOrganization,
)
from app.models.user import User
from app.partner_foundation.rbac import default_permissions_for_role, org_role_has_permission
from app.partner_foundation.service import ensure_default_organization, seed_organization_roles
from app.web_gateway.routing import workspace_path_for_role

# Organization-level feature flags (Epic 2 baseline; Epic 3 expands registry).
ORG_TYPE_FEATURES: dict[str, list[str]] = {
    "DXCON_INTERNAL": [
        "LABORATORY",
        "HOME_COLLECTION",
        "DOCTOR_CONSULTATION",
        "PRESCRIPTION",
        "FOLLOW_UP",
        "MARKETPLACE",
        "FINANCE",
        "AI_ASSISTANT",
    ],
    "CLINIC": [
        "HOME_COLLECTION",
        "DOCTOR_CONSULTATION",
        "MARKETPLACE",
        "QR_PAYMENT",
    ],
    "HOSPITAL": [
        "LABORATORY",
        "HOME_COLLECTION",
        "DOCTOR_CONSULTATION",
        "IMAGING",
        "MARKETPLACE",
    ],
    "LABORATORY": [
        "LABORATORY",
        "LIS_REALTIME",
        "HOME_COLLECTION",
    ],
    "PARTNER": ["LABORATORY", "HOME_COLLECTION", "MARKETPLACE"],
    "CORPORATE": ["MARKETPLACE", "FINANCE"],
    "INSURANCE": ["MARKETPLACE", "FINANCE"],
}


class AuthContextError(ValueError):
    def __init__(self, message: str, code: str = "AUTH_CONTEXT_ERROR", status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


def _membership_status(membership: OrganizationUser, org: PartnerOrganization) -> str:
    if not membership.active:
        return "disabled"
    if org.status == ORG_STATUS_SUSPENDED:
        return "suspended"
    if org.status != ORG_STATUS_ACTIVE:
        return "inactive"
    return "active"


def list_user_memberships(user: User) -> list[dict[str, Any]]:
    ensure_default_organization()
    seed_organization_roles()
    rows = (
        OrganizationUser.query.filter_by(user_id=user.id)
        .order_by(OrganizationUser.created_at.asc())
        .all()
    )
    memberships: list[dict[str, Any]] = []
    for row in rows:
        org = PartnerOrganization.query.get(row.organization_id)
        if not org:
            continue
        memberships.append(
            {
                "membership_id": row.id,
                "organization_id": org.id,
                "organization_name": org.organization_name,
                "organization_type": org.organization_type,
                "organization_code": org.organization_code,
                "organization_status": org.status,
                "role_code": row.role_code,
                "membership_status": _membership_status(row, org),
                "default_workspace": workspace_path_for_role(user.role),
                "department_id": None,
                "team_id": None,
            }
        )
    if not memberships and user.organization_id:
        org = PartnerOrganization.query.get(user.organization_id)
        if org:
            memberships.append(
                {
                    "membership_id": None,
                    "organization_id": org.id,
                    "organization_name": org.organization_name,
                    "organization_type": org.organization_type,
                    "organization_code": org.organization_code,
                    "organization_status": org.status,
                    "role_code": "VIEWER",
                    "membership_status": "active" if org.status == ORG_STATUS_ACTIVE else org.status,
                    "default_workspace": workspace_path_for_role(user.role),
                    "department_id": None,
                    "team_id": None,
                }
            )
    return memberships


def _resolve_active_membership(
    user: User,
    organization_id: str | None,
) -> tuple[PartnerOrganization | None, OrganizationUser | None, dict[str, Any] | None]:
    memberships = list_user_memberships(user)
    if not memberships:
        return None, None, None

    target_id = organization_id or user.organization_id or memberships[0]["organization_id"]
    selected = next((m for m in memberships if m["organization_id"] == target_id), None)
    if not selected:
        raise AuthContextError("Organization membership not found", "MEMBERSHIP_NOT_FOUND", 403)

    if selected["membership_status"] == "disabled":
        raise AuthContextError("Membership is disabled", "MEMBERSHIP_DISABLED", 403)
    if selected["membership_status"] == "suspended":
        raise AuthContextError("Organization is suspended", "ORGANIZATION_SUSPENDED", 403)
    if selected["membership_status"] != "active":
        raise AuthContextError("Organization is not active", "ORGANIZATION_INACTIVE", 403)

    org = PartnerOrganization.query.get(selected["organization_id"])
    membership = None
    if selected.get("membership_id"):
        membership = OrganizationUser.query.get(selected["membership_id"])
    return org, membership, selected


def switch_organization(user: User, organization_id: str) -> dict[str, Any]:
    org, membership, selected = _resolve_active_membership(user, organization_id)
    if not org or not selected:
        raise AuthContextError("No valid organization context", "ORGANIZATION_REQUIRED", 403)

    user.organization_id = org.id
    if membership:
        membership.last_login = datetime.utcnow()
    db.session.flush()
    return build_capabilities(user, org.id)


def _merge_permissions(user: User, org_role_code: str | None) -> list[str]:
    platform = get_role_permissions(user.role)
    org_perms = default_permissions_for_role(org_role_code or "")
    merged = set(platform) | set(org_perms)
    if role_has_permission(user.role, "*") or user.role in {"SUPER_ADMIN", "SYSTEM_ADMIN"}:
        merged.add("*")
    return sorted(merged)


def _features_for_org(org: PartnerOrganization | None) -> list[str]:
    if not org:
        return []
    return list(ORG_TYPE_FEATURES.get(org.organization_type, []))


def build_capabilities(user: User, organization_id: str | None = None) -> dict[str, Any]:
    org, membership, selected = _resolve_active_membership(user, organization_id)
    org_role = selected["role_code"] if selected else None
    permissions = _merge_permissions(user, org_role)
    workspace = workspace_path_for_role(user.role)

    def can(permission: str) -> bool:
        if "*" in permissions:
            return True
        if role_has_permission(user.role, permission):
            return True
        return org_role_has_permission(org_role or "", permission)

    effective = [p for p in permissions if p != "*" or role_has_permission(user.role, "*")]

    return {
        "user": user.to_dict(),
        "organization": org.to_dict() if org else None,
        "membership": {
            "membership_id": selected.get("membership_id") if selected else None,
            "organization_id": selected["organization_id"] if selected else None,
            "role_code": org_role,
            "membership_status": selected["membership_status"] if selected else None,
            "department_id": selected.get("department_id") if selected else None,
            "team_id": selected.get("team_id") if selected else None,
        },
        "workspace": workspace,
        "default_workspace": workspace,
        "permissions": effective,
        "features": _features_for_org(org),
        "can": {
            "platform_role": user.role,
            "organization_role": org_role,
        },
    }


def current_user_payload(user: User) -> dict[str, Any]:
    memberships = list_user_memberships(user)
    active_org_id = user.organization_id
    if not active_org_id and memberships:
        active_org_id = memberships[0]["organization_id"]
    return {
        "user": user.to_dict(),
        "active_organization_id": active_org_id,
        "memberships": memberships,
        "requires_organization_selection": len(memberships) > 1 and not user.organization_id,
    }
