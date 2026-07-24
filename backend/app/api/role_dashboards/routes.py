"""Role dashboard REST API — go-live operational KPIs."""

from __future__ import annotations

from flask import Blueprint, request, session

from app.core.authz import roles_required
from app.role_dashboards.security import ROLE_DASHBOARD_ROLES
from app.role_dashboards.service import RoleDashboardError, build_role_dashboard, role_can_access

role_dashboards_bp = Blueprint(
    "role_dashboards",
    __name__,
    url_prefix="/api/v1/role-dashboards",
)

_ALL_DASHBOARD_ROLES = frozenset().union(*ROLE_DASHBOARD_ROLES.values())


def _actor_role() -> str | None:
    return session.get("role") or request.headers.get("X-User-Role")


def _session_ok() -> bool:
    role = session.get("role") or ""
    return bool(session.get("user_id")) and role in _ALL_DASHBOARD_ROLES


def _require_dashboard_access(fn):
    """Dual auth: session role OR JWT with any dashboard-capable role."""
    jwt_wrapped = roles_required(*_ALL_DASHBOARD_ROLES)(fn)

    def wrapper(*args, **kwargs):
        if _session_ok():
            return fn(*args, **kwargs)
        return jwt_wrapped(*args, **kwargs)

    wrapper.__name__ = fn.__name__
    return wrapper


@role_dashboards_bp.route("/<role_key>", methods=["GET"])
@_require_dashboard_access
def get_role_dashboard(role_key: str):
    actor = _actor_role()
    # Prefer JWT claim when session absent
    if not actor:
        try:
            from flask_jwt_extended import get_jwt

            actor = (get_jwt() or {}).get("role")
        except Exception:
            actor = None

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
@_require_dashboard_access
def get_summary():
    """Cross-cutting operational summary for admin/ops (aggregates only)."""
    actor = _actor_role()
    if not actor:
        try:
            from flask_jwt_extended import get_jwt

            actor = (get_jwt() or {}).get("role")
        except Exception:
            actor = None
    if actor not in {"SUPER_ADMIN", "ADMIN", "PLATFORM_ADMIN", "LAB_SUPERVISOR", "LAB_MANAGER"}:
        return {"success": False, "error": "Insufficient role for summary"}, 403
    try:
        payload = build_role_dashboard("admin")
    except RoleDashboardError as exc:
        return {"success": False, "error": exc.message}, exc.status_code
    return {"success": True, "data": payload}, 200
