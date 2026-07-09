"""Production web gateway UI — Sprint 011 workspace home pages."""

from __future__ import annotations

import html

from flask import Blueprint, session

from app.core.web_authz import web_roles_required
from app.utils.auth import login_required
from app.web.launch_ui_lib import action_grid, metric_cards, module_intro, render_page
from app.web_gateway.routing import workspace_path_for_role

production_gateway_web_bp = Blueprint("production_gateway_web", __name__)

ADMIN_ROLES = frozenset({"SUPER_ADMIN", "DXCON_ADMIN", "ADMIN", "SYSTEM_ADMIN"})


def _h(v: str) -> str:
    return html.escape(str(v))


def workspace_home_body() -> str:
    role = (session.get("role") or "GUEST").upper()
    target = workspace_path_for_role(role)
    return (
        module_intro("Workspace", f"Signed in as {_h(session.get('email') or 'user')} · role {_h(role)}")
        + metric_cards([
            ("Your workspace", target),
            ("Role", role),
            ("Status", "ACTIVE"),
        ])
        + action_grid([
            ("Go to role workspace", target, "Primary dashboard for your role"),
            ("Executive", "/app/executive", "Operations overview"),
            ("Operations", "/app/operations", "Incidents and support"),
            ("System", "/app/system", "Health and runbooks"),
        ])
        + '<p class="launch-hint">Unknown or multi-role users land here. Configure role routing in the production gateway.</p>'
    )


def admin_workspace_body() -> str:
    return (
        module_intro("Administration", "Platform administration, organizations, and partner governance.")
        + action_grid([
            ("Organizations", "/app/admin/organizations", "Tenant and org setup"),
            ("Partner users", "/app/admin/partner-users", "Partner accounts"),
            ("Contracts", "/app/admin/partner-contracts", "Commercial agreements"),
            ("Price lists", "/app/admin/partner-price-lists", "Partner pricing"),
            ("Settings", "/app/admin/settings", "Platform settings"),
            ("Permission matrix", "/app/admin/permission-matrix", "RBAC overview"),
            ("Audit", "/app/admin/organization-audit", "Organization audit log"),
        ])
        + metric_cards([
            ("Workspace", "Admin"),
            ("Access", "SUPER_ADMIN / ADMIN"),
            ("Environment", "Production-ready"),
        ])
    )


@production_gateway_web_bp.route("/app")
@login_required
def workspace_home():
    return render_page("Workspace", workspace_home_body(), active_nav="/app")


@production_gateway_web_bp.route("/app/admin")
@login_required
@web_roles_required(*ADMIN_ROLES)
def admin_workspace_home():
    return render_page("Administration", admin_workspace_body(), active_nav="/app/admin/organizations")
