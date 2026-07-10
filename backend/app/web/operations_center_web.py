"""Operations Center UI — Release 1.0 Operations Excellence."""

from __future__ import annotations

import html

from flask import Blueprint

from app.core.web_authz import web_roles_required
from app.operations_center.security import OPS_CENTER_READ_ROLES
from app.operations_center.service import dashboard
from app.utils.auth import login_required
from app.web.launch_ui_lib import action_grid, metric_cards, render_page, status_badge, table_section
from app.web.portal_layout import PORTAL_RESPONSIVE_CSS

operations_center_web_bp = Blueprint("operations_center_web", __name__)


def _h(v: str) -> str:
    return html.escape(str(v))


def _ops_nav(active: str = "") -> str:
    links = [
        ("Operations", "/app/operations"),
        ("Monitoring", "/app/monitoring"),
        ("Audit", "/app/audit-center"),
        ("Support", "/app/support"),
    ]
    items = [
        f'<a class="{"launch-btn launch-btn-sm" if href == active else "launch-btn-outline launch-btn-sm"}" href="{href}">{_h(label)}</a>'
        for label, href in links
    ]
    return PORTAL_RESPONSIVE_CSS + '<div class="portal-nav">' + "".join(items) + "</div>"


@operations_center_web_bp.route("/app/operations")
@login_required
@web_roles_required(*OPS_CENTER_READ_ROLES)
def operations_center_page():
    data = dashboard()
    w = data["widgets"]
    body = (
        _ops_nav("/app/operations")
        + metric_cards([
            ("Open Incidents", w["open_incidents"]),
            ("Open Support Tickets", w["open_support_tickets"]),
            ("System Health", w["system_health"]),
            ("Deployments", w["deployments"]),
            ("Failed Jobs", w["failed_jobs"]),
            ("Critical Alerts", w["critical_alerts"]),
            ("Pending Customer Requests", w["pending_customer_requests"]),
        ])
        + table_section(
            "Open Incidents",
            ["Code", "Type", "Severity", "Status"],
            [
                [_h(i.get("incident_code", "")), _h(i.get("incident_type", "")), status_badge(i.get("severity", "")), status_badge(i.get("status", ""))]
                for i in data.get("recent_incidents", [])
            ] or [["—", "—", status_badge("none"), status_badge("none")]],
        )
        + table_section(
            "Open Support Tickets",
            ["Code", "Subject", "Priority", "Status"],
            [
                [_h(t.get("ticket_code", "")), _h(t.get("subject", "")), status_badge(t.get("priority", "")), status_badge(t.get("status", ""))]
                for t in data.get("recent_tickets", [])
            ] or [["—", "—", status_badge("none"), status_badge("none")]],
        )
        + table_section(
            "Critical Alerts",
            ["Code", "Type", "Severity", "Status"],
            [
                [_h(a.get("alert_code", "")), _h(a.get("alert_type", "")), status_badge(a.get("severity", "")), status_badge(a.get("status", ""))]
                for a in data.get("recent_alerts", [])
            ] or [["—", "—", status_badge("none"), status_badge("none")]],
        )
        + table_section(
            "Failed Jobs",
            ["Run", "Status", "Retries", "Error"],
            [
                [_h(j.get("run_code", "")), status_badge(j.get("status", "")), _h(j.get("retry_count", 0)), _h((j.get("error_message") or "")[:60])]
                for j in data.get("recent_failed_jobs", [])
            ] or [["—", status_badge("none"), "—", "—"]],
        )
        + table_section(
            "Recent Deployments",
            ["Version", "Environment", "Status", "When"],
            [
                [_h(d.get("version", "")), _h(d.get("environment", "")), status_badge(d.get("status", "")), _h(d.get("created_at") or "—")]
                for d in data.get("recent_deployments", [])
            ] or [["—", "—", status_badge("none"), "—"]],
        )
        + table_section(
            "Pending Customer Requests",
            ["Code", "Title", "Type", "Status"],
            [
                [_h(r.get("request_code", "")), _h(r.get("title", "")), status_badge(r.get("request_type", "")), status_badge(r.get("status", ""))]
                for r in data.get("pending_requests", [])
            ] or [["—", "—", status_badge("none"), status_badge("none")]],
        )
        + action_grid([
            ("Monitoring", "/app/monitoring", "Live system health"),
            ("Audit Center", "/app/audit-center", "Global audit log"),
            ("Support Center", "/app/support", "Tickets & help"),
            ("Backup", "/app/backup", "Backup & restore"),
        ])
        + '<p class="launch-hint">API: <code>/api/v1/operations-center/dashboard</code></p>'
    )
    return render_page("Operations Center", body, active_nav="/app/operations")
