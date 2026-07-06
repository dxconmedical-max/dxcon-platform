"""Executive platform UI — Sprint 010."""

from __future__ import annotations

import html

from flask import Blueprint, request

from app.core.web_authz import web_roles_required
from app.executive_platform.security import AUDIT_READ_ROLES, CRM_READ_ROLES, EXECUTIVE_READ_ROLES, FINANCE_READ_ROLES, MONITORING_READ_ROLES, PILOT_READ_ROLES
from app.executive_platform.service import (
    admin_settings,
    audit_center,
    backup_dashboard,
    crm_dashboard,
    executive_dashboard,
    finance_dashboard,
    launch_checklist,
    operational_monitoring,
    pilot_wizard,
    security_report,
    verify_checklist_item,
)
from app.extensions.db import db
from app.utils.auth import login_required
from app.web.launch_ui_lib import action_grid, metric_cards, render_page, status_badge, table_section
from app.web.portal_layout import PORTAL_RESPONSIVE_CSS

executive_platform_web_bp = Blueprint("executive_platform_web", __name__)


def _h(v: str) -> str:
    return html.escape(str(v))


def _exec_nav(active: str = "") -> str:
    links = [
        ("Executive", "/app/executive"),
        ("CRM", "/app/crm"),
        ("Finance", "/app/finance"),
        ("Monitoring", "/app/monitoring"),
        ("Audit", "/app/audit-center"),
        ("Admin", "/app/admin/settings"),
        ("Pilot", "/app/pilot/wizard"),
        ("Support", "/app/support"),
    ]
    items = [f'<a class="{"launch-btn launch-btn-sm" if href == active else "launch-btn-outline launch-btn-sm"}" href="{href}">{_h(label)}</a>' for label, href in links]
    return PORTAL_RESPONSIVE_CSS + '<div class="portal-nav">' + "".join(items) + "</div>"


@executive_platform_web_bp.route("/app/executive")
@executive_platform_web_bp.route("/executive-v10")
@login_required
@web_roles_required(*EXECUTIVE_READ_ROLES)
def executive_page():
    data = executive_dashboard()
    w = data["widgets"]
    body = (
        _exec_nav("/app/executive")
        + metric_cards([
            ("Revenue Today", f"{w['revenue_today']:,.0f}"),
            ("Revenue MTD", f"{w['revenue_this_month']:,.0f}"),
            ("Orders Today", w["orders_today"]),
            ("Orders MTD", w["orders_this_month"]),
            ("Patients", w["patients"]),
            ("Pending Reports", w["pending_reports"]),
            ("Critical", w["critical_results"]),
            ("Collections", w["sample_collections"]),
        ])
        + table_section("Revenue Trend (7d)", ["Date", "Revenue"], [
            [_h(r["date"]), f"{r['revenue']:,.0f}"] for r in data["charts"]["revenue_trend"]
        ])
        + table_section("Order Trend (7d)", ["Date", "Orders"], [
            [_h(r["date"]), str(r["orders"])] for r in data["charts"]["order_trend"]
        ])
        + action_grid([
            ("CRM", "/app/crm", "Sales pipeline"),
            ("Finance", "/app/finance", "Revenue & billing"),
            ("Monitoring", "/app/monitoring", "System health"),
            ("Audit Center", "/app/audit-center", "Global audit log"),
        ])
    )
    return render_page("Executive Dashboard", body, active_nav="/app/executive")


@executive_platform_web_bp.route("/app/crm")
@login_required
@web_roles_required(*CRM_READ_ROLES)
def crm_page():
    data = crm_dashboard()
    funnel_rows = [[_h(k), str(v)] for k, v in data.get("pipeline", {}).items()]
    body = (
        _exec_nav("/app/crm")
        + metric_cards([
            ("Leads", data.get("leads", 0)),
            ("Opportunities", data.get("opportunities", 0)),
            ("Conversion", f"{data.get('conversion_rate', 0)}%"),
            ("Monthly Sales", f"{data.get('monthly_sales', 0):,.0f}"),
        ])
        + table_section("Sales Pipeline", ["Stage", "Count"], funnel_rows or [["—", "0"]])
        + f'<p class="launch-hint">Modules: {", ".join(data.get("modules", []))}</p>'
    )
    return render_page("CRM", body, active_nav="/app/executive")


@executive_platform_web_bp.route("/app/finance")
@login_required
@web_roles_required(*FINANCE_READ_ROLES)
def finance_page():
    data = finance_dashboard()
    body = (
        _exec_nav("/app/finance")
        + metric_cards([
            ("Revenue MTD", f"{data['revenue_dashboard']['revenue_mtd']:,.0f}"),
            ("Paid Invoices", data["payment_dashboard"]["paid_count"]),
            ("Pending", data["payment_dashboard"]["pending_count"]),
            ("Outstanding", f"{data['outstanding_balance']:,.0f}"),
        ])
        + '<div class="launch-card"><h3>Corporate &amp; Insurance Billing</h3><p>Placeholder — configure in Release 2.0</p></div>'
    )
    return render_page("Finance", body, active_nav="/app/executive")


@executive_platform_web_bp.route("/app/monitoring")
@login_required
@web_roles_required(*MONITORING_READ_ROLES)
def monitoring_page():
    data = operational_monitoring()
    rows = [[_h(k.replace("_", " ").title()), status_badge(str(v) if not isinstance(v, dict) else "ready")] for k, v in data.items() if k != "integration_status"]
    body = _exec_nav("/app/monitoring") + table_section("Operational Monitoring", ["Component", "Status"], rows)
    return render_page("Monitoring", body, active_nav="/app/executive")


@executive_platform_web_bp.route("/app/audit-center")
@login_required
@web_roles_required(*AUDIT_READ_ROLES)
def audit_page():
    result = audit_center(q=request.args.get("q"), user=request.args.get("user"))
    rows = [[_h(r["action"]), _h(r["object_type"]), _h(r["user_email"] or ""), _h(r["created_at"] or "")] for r in result["data"][:30]]
    body = (
        _exec_nav("/app/audit-center")
        + f'<form method="GET" class="launch-card"><input name="q" placeholder="Search audit..." class="launch-input"/> <button class="launch-btn launch-btn-sm" type="submit">Search</button></form>'
        + table_section("Audit Log", ["Action", "Object", "User", "Time"], rows or [["—"] * 4])
    )
    return render_page("Audit Center", body, active_nav="/app/executive")


@executive_platform_web_bp.route("/app/admin/settings")
@login_required
@web_roles_required(*EXECUTIVE_READ_ROLES)
def admin_page():
    settings = admin_settings()
    rows = [[_h(k), _h(str(v)[:80])] for k, v in settings.items()]
    body = _exec_nav("/app/admin/settings") + table_section("Administration", ["Section", "Config"], rows)
    return render_page("Administration", body, active_nav="/app/executive")


@executive_platform_web_bp.route("/app/pilot/wizard")
@login_required
@web_roles_required(*PILOT_READ_ROLES)
def pilot_page():
    data = pilot_wizard()
    rows = [[_h(c["label"]), status_badge("done" if c.get("done") else "pending")] for c in data.get("checklist", [])]
    body = _exec_nav("/app/pilot/wizard") + table_section("Pilot Wizard Checklist", ["Step", "Status"], rows)
    return render_page("Pilot Wizard", body, active_nav="/app/executive")


@executive_platform_web_bp.route("/app/backup")
@login_required
@web_roles_required(*EXECUTIVE_READ_ROLES)
def backup_page():
    data = backup_dashboard()
    body = _exec_nav() + f'<div class="launch-card"><p>Manual backup: {data["manual_backup"]} · Scheduled: {data["scheduled_backup"]}</p></div>'
    return render_page("Backup", body, active_nav="/app/executive")


@executive_platform_web_bp.route("/app/support")
@login_required
def support_page():
    body = (
        _exec_nav("/app/support")
        + action_grid([
            ("FAQ", "/app/support#faq", "Common questions"),
            ("Release Notes", "/app/support#releases", "Version history"),
            ("System Status", "/app/monitoring", "Live status"),
            ("Contact", "mailto:support@dxcon.test", "Email support"),
        ])
        + '<div class="launch-card" id="faq"><h3>FAQ</h3><p>How do I onboard a new laboratory? Use the Pilot Wizard.</p></div>'
    )
    return render_page("Support Center", body, active_nav="/app/executive")


@executive_platform_web_bp.route("/app/launch-checklist")
@login_required
@web_roles_required(*EXECUTIVE_READ_ROLES)
def launch_checklist_page():
    data = launch_checklist()
    rows = [[_h(i["label"]), status_badge(i.get("status", "pending")), _h(i.get("category", ""))] for i in data.get("items", [])]
    body = _exec_nav() + table_section("Launch Checklist", ["Item", "Status", "Category"], rows)
    return render_page("Launch Checklist", body, active_nav="/app/executive")
