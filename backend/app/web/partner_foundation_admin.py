"""Partner foundation web UI — portals and administration."""

from __future__ import annotations

import html

from flask import Blueprint, request, session

from app.core.web_authz import web_roles_required
from app.extensions.db import db
from app.models.audit_log import AuditLog
from app.partner_foundation.security import PARTNER_READ_ROLES, PARTNER_WRITE_ROLES
from app.partner_foundation.service import (
    ensure_default_organization,
    organization_dashboard,
    permission_matrix,
    query_organizations,
    seed_organization_roles,
)
from app.models.partner_foundation import OrganizationPriceList, OrganizationUser, PartnerContract
from app.utils.auth import login_required
from app.web.launch_ui_lib import metric_cards, render_page, status_badge, table_section

partner_foundation_web_bp = Blueprint("partner_foundation_web", __name__)

ADMIN_MENU: tuple[tuple[str, str], ...] = (
    ("Organizations", "organizations"),
    ("Partner Users", "partner-users"),
    ("Partner Contracts", "partner-contracts"),
    ("Partner Price Lists", "partner-price-lists"),
    ("Organization Settings", "organization-settings"),
    ("Permission Matrix", "permission-matrix"),
    ("Organization Audit", "organization-audit"),
)

PORTAL_PATHS = {
    "partner": "/app/partner",
    "clinic": "/app/clinic",
    "doctor": "/app/partner/doctor",
    "corporate": "/app/corporate",
    "insurance": "/app/insurance",
}


def _admin_nav(active: str = "") -> str:
    links = ['<a class="launch-btn-outline launch-btn-sm" href="/app/admin/organizations">Administration</a>']
    for label, slug in ADMIN_MENU:
        href = f"/app/admin/{slug}"
        css = "launch-btn launch-btn-sm" if active == slug else "launch-btn-outline launch-btn-sm"
        links.append(f'<a class="{css}" href="{href}">{html.escape(label)}</a>')
    return '<div class="launch-action-row" style="flex-wrap:wrap;margin-bottom:20px;">' + "".join(links) + "</div>"


def _portal_body(portal: str, title: str) -> str:
    org_id = session.get("organization_id")
    if not org_id:
        org = ensure_default_organization()
        org_id = org.id
        session["organization_id"] = org_id
    dash = organization_dashboard(org_id, portal)
    org = dash["organization"]
    widgets = dash.get("widgets", [])
    metrics = dash.get("metrics", {})
    widget_html = "".join(f"<li>{html.escape(w.replace('_', ' ').title())}</li>" for w in widgets)
    cards = metric_cards([(k.replace("_", " ").title(), v) for k, v in metrics.items()])
    return (
        f'<div class="launch-card"><h3>{html.escape(title)}</h3>'
        f'<p>Organization: <strong>{html.escape(org.get("organization_name", ""))}</strong> '
        f'({html.escape(org.get("organization_code", ""))})</p></div>'
        + cards
        + f'<div class="launch-card"><h4>Widgets</h4><ul>{widget_html}</ul></div>'
        + f'<p class="launch-hint">API: <code>/api/v1/partner/dashboard/{html.escape(portal)}</code></p>'
    )


@partner_foundation_web_bp.route("/app/partner")
@login_required
@web_roles_required(*PARTNER_READ_ROLES)
def partner_portal():
    return render_page("Partner Portal", _portal_body("partner", "Partner Overview"), active_nav="/app/partner")


@partner_foundation_web_bp.route("/app/clinic")
@login_required
@web_roles_required(*PARTNER_READ_ROLES)
def clinic_portal():
    return render_page("Clinic Dashboard", _portal_body("clinic", "Clinic Dashboard"), active_nav="/app/clinic")


@partner_foundation_web_bp.route("/app/partner/doctor")
@login_required
@web_roles_required(*PARTNER_READ_ROLES)
def doctor_partner_portal():
    return render_page("Doctor Dashboard", _portal_body("doctor", "Doctor Dashboard"), active_nav="/app/partner/doctor")


@partner_foundation_web_bp.route("/app/corporate")
@login_required
@web_roles_required(*PARTNER_READ_ROLES)
def corporate_portal():
    return render_page("Corporate Dashboard", _portal_body("corporate", "Corporate Dashboard"), active_nav="/app/corporate")


@partner_foundation_web_bp.route("/app/insurance")
@login_required
@web_roles_required(*PARTNER_READ_ROLES)
def insurance_portal():
    return render_page("Insurance Dashboard", _portal_body("insurance", "Insurance Dashboard"), active_nav="/app/insurance")


@partner_foundation_web_bp.route("/app/admin/organizations")
@login_required
@web_roles_required(*PARTNER_READ_ROLES)
def admin_organizations():
    result = query_organizations(page=int(request.args.get("page", 1)), per_page=50)
    rows = [
        [
            html.escape(r.get("organization_code", "")),
            html.escape(r.get("organization_name", "")),
            html.escape(r.get("organization_type", "")),
            status_badge(r.get("status", "active")),
        ]
        for r in result["data"]
    ]
    body = (
        _admin_nav("organizations")
        + table_section("Organizations", ["Code", "Name", "Type", "Status"], rows or [["—", "—", "—", status_badge("none")]])
        + '<p class="launch-hint">CRUD via <code>POST /api/v1/partner/organizations</code></p>'
    )
    return render_page("Organizations", body, active_nav="/app/admin/organizations")


@partner_foundation_web_bp.route("/app/admin/partner-users")
@login_required
@web_roles_required(*PARTNER_READ_ROLES)
def admin_partner_users():
    memberships = OrganizationUser.query.limit(100).all()
    rows = [
        [
            html.escape(m.organization_id),
            html.escape(m.user_id),
            html.escape(m.role_code),
            status_badge("active" if m.active else "inactive"),
        ]
        for m in memberships
    ]
    body = _admin_nav("partner-users") + table_section(
        "Partner Users", ["Organization", "User", "Role", "Status"], rows or [["—", "—", "—", status_badge("none")]]
    )
    return render_page("Partner Users", body, active_nav="/app/admin/partner-users")


@partner_foundation_web_bp.route("/app/admin/partner-contracts")
@login_required
@web_roles_required(*PARTNER_READ_ROLES)
def admin_partner_contracts():
    contracts = PartnerContract.query.limit(100).all()
    rows = [
        [
            html.escape(c.contract_code),
            html.escape(c.organization_id),
            html.escape(c.status or ""),
            str(c.discount_percent or 0),
        ]
        for c in contracts
    ]
    body = _admin_nav("partner-contracts") + table_section(
        "Partner Contracts", ["Code", "Organization", "Status", "Discount %"], rows or [["—", "—", "—", "0"]]
    )
    return render_page("Partner Contracts", body, active_nav="/app/admin/partner-contracts")


@partner_foundation_web_bp.route("/app/admin/partner-price-lists")
@login_required
@web_roles_required(*PARTNER_READ_ROLES)
def admin_partner_price_lists():
    pls = OrganizationPriceList.query.limit(100).all()
    rows = [
        [
            html.escape(p.organization_id),
            html.escape(p.price_tier),
            html.escape(p.price_list_code),
            status_badge(p.status or "active"),
        ]
        for p in pls
    ]
    body = _admin_nav("partner-price-lists") + table_section(
        "Partner Price Lists", ["Organization", "Tier", "Price List", "Status"], rows or [["—", "—", "—", status_badge("none")]]
    )
    return render_page("Partner Price Lists", body, active_nav="/app/admin/partner-price-lists")


@partner_foundation_web_bp.route("/app/admin/organization-settings")
@login_required
@web_roles_required(*PARTNER_READ_ROLES)
def admin_organization_settings():
    org = ensure_default_organization()
    seed_organization_roles()
    db.session.commit()
    body = (
        _admin_nav("organization-settings")
        + f'<div class="launch-card"><h3>Default Organization</h3><pre>{html.escape(str(org.to_dict()))}</pre></div>'
        + '<p class="launch-hint">Session organization_id drives tenant scope for queries.</p>'
    )
    return render_page("Organization Settings", body, active_nav="/app/admin/organization-settings")


@partner_foundation_web_bp.route("/app/admin/permission-matrix")
@login_required
@web_roles_required(*PARTNER_READ_ROLES)
def admin_permission_matrix():
    matrix = permission_matrix()
    rows = []
    for role in matrix.get("roles", []):
        perms = ", ".join(role.get("permissions", [])[:8])
        if len(role.get("permissions", [])) > 8:
            perms += "…"
        rows.append([html.escape(role.get("role_code", "")), html.escape(role.get("role_name", "")), html.escape(perms)])
    body = _admin_nav("permission-matrix") + table_section("Permission Matrix", ["Role", "Name", "Permissions"], rows)
    return render_page("Permission Matrix", body, active_nav="/app/admin/permission-matrix")


@partner_foundation_web_bp.route("/app/admin/organization-audit")
@login_required
@web_roles_required(*PARTNER_READ_ROLES)
def admin_organization_audit():
    logs = (
        AuditLog.query.filter(AuditLog.action.like("organization.%"))
        .order_by(AuditLog.created_at.desc())
        .limit(50)
        .all()
    )
    rows = [
        [
            html.escape(log.action or ""),
            html.escape(log.object_type or ""),
            html.escape(str(log.object_id or "")),
            html.escape(log.user_email or ""),
        ]
        for log in logs
    ]
    body = _admin_nav("organization-audit") + table_section(
        "Organization Audit", ["Action", "Object", "ID", "Actor"], rows or [["—", "—", "—", "—"]]
    )
    return render_page("Organization Audit", body, active_nav="/app/admin/organization-audit")
