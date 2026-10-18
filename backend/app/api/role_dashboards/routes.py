"""Role dashboard REST API — go-live operational KPIs."""

from __future__ import annotations

from flask import Blueprint, request

from app.core.authenticated_identity import (
    AuthenticatedIdentity,
    bind_authenticated_identity,
    get_authenticated_identity,
)
from app.core.authz import roles_required
from app.role_dashboards.security import ROLE_DASHBOARD_ROLES
from app.role_dashboards.service import RoleDashboardError, build_role_dashboard, role_can_access

role_dashboards_bp = Blueprint(
    "role_dashboards",
    __name__,
    url_prefix="/api/v1/role-dashboards",
)

_ALL_DASHBOARD_ROLES = frozenset().union(*ROLE_DASHBOARD_ROLES.values())
_SUMMARY_ROLES = frozenset(
    {"SUPER_ADMIN", "ADMIN", "PLATFORM_ADMIN", "LAB_SUPERVISOR", "LAB_MANAGER"}
)


def _actor_platform_role() -> str | None:
    """Effective role from authenticated identity only — never X-User-Role / query role."""
    identity = get_authenticated_identity()
    if identity is None:
        result = bind_authenticated_identity()
        if not isinstance(result, AuthenticatedIdentity):
            return None
        identity = result
    return identity.platform_role


@role_dashboards_bp.route("/<role_key>", methods=["GET"])
@roles_required(*_ALL_DASHBOARD_ROLES)
def get_role_dashboard(role_key: str):
    actor = _actor_platform_role()
    # Path role_key is a dashboard *view* selector, not an authorization grant.
    # Client ?role= / X-User-Role cannot elevate access.
    if not role_can_access(actor, role_key):
        return {
            "success": False,
            "error": f"Role {actor or 'unknown'} cannot access {role_key} dashboard",
        }, 403

    try:
        payload = build_role_dashboard(
            role_key,
            scoped_collector_id=request.headers.get("X-Collector-Id")
            or request.args.get("collector_id"),
            patient_code=request.headers.get("X-Patient-Code")
            or request.args.get("patient_code"),
        )
    except RoleDashboardError as exc:
        return {"success": False, "error": exc.message}, exc.status_code

    return {"success": True, "data": payload}, 200


@role_dashboards_bp.route("/summary", methods=["GET"])
@roles_required(*_SUMMARY_ROLES)
def get_summary():
    """Cross-cutting operational summary for admin/ops (aggregates only)."""
    try:
        payload = build_role_dashboard("admin")
    except RoleDashboardError as exc:
        return {"success": False, "error": exc.message}, exc.status_code
    return {"success": True, "data": payload}, 200
