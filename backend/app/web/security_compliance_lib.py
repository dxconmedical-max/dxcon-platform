"""Security & Compliance web rendering helpers — Phase 5 Sprint 5.1."""

from __future__ import annotations

import html
import json

from app.services import security_compliance_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

SECURITY_NAV = (
    ("Overview", "/security-compliance"),
    ("Secrets", "/security-compliance/secrets"),
    ("API Keys", "/security-compliance/api-keys"),
    ("JWT", "/security-compliance/jwt"),
    ("RBAC", "/security-compliance/rbac"),
    ("Audit Logs", "/security-compliance/audit"),
    ("Timeline", "/security-compliance/timeline"),
    ("Failed Logins", "/security-compliance/failed-logins"),
    ("IP Whitelist", "/security-compliance/ip-whitelist"),
    ("Rate Limits", "/security-compliance/rate-limits"),
    ("PHI Access", "/security-compliance/phi-access"),
    ("Compliance", "/security-compliance/compliance"),
)


def security_styles() -> str:
    return pilot_styles() + """
    .feature-list { columns:2; gap:24px; font-size:13px; color:#334155; }
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; max-width:100%; white-space:pre-wrap; }
    .muted-note { color:#64748b; font-size:13px; margin-bottom:16px; }
    .status-pass { color:#047857; font-weight:700; }
    .status-warn { color:#b45309; font-weight:700; }
    """


def render_security_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in SECURITY_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{security_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted-note">Enterprise pilot security · Phase 5 Sprint 5.1</div>
            {body_html}
        </div>
    </body>
    </html>
    """


def _table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "<p class='muted'>No records.</p>"
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table><tr>{head}</tr>{body}</table>"


def build_dashboard_body() -> str:
    data = svc.dashboard_payload()
    summary = data["summary"]
    cards = metric_cards(
        [
            ("Readiness Score", summary["readiness_score"]),
            ("API Keys", summary["api_keys_total"]),
            ("Need Rotation", summary["keys_needing_rotation"]),
            ("Active JWT Sessions", summary["active_jwt_sessions"]),
            ("Audit Entries", summary["audit_entries"]),
            ("Failed Logins", summary["failed_login_attempts"]),
            ("PHI Access Logs", summary["phi_access_entries"]),
            ("Rate Limit Max", summary["rate_limit_max"]),
        ]
    )
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    status_class = "status-pass" if data["status"] == "OK" else "status-warn"
    return f"""
    {page_header("Security & Compliance", "Prepare DxCon for enterprise pilot security.")}
    <div class="card"><strong>Status:</strong> <span class="{status_class}">{html.escape(data["status"])}</span></div>
    {cards}
    <div class="card" style="margin-top:20px;">
        <h3>Sprint 5.1 Features</h3>
        <ul class="feature-list">{features}</ul>
    </div>
    """


def build_secrets_body() -> str:
    data = svc.secret_management_audit()
    rows = [
        [html.escape(item["setting_key"]), html.escape(item["category"] or ""), html.escape(item["masked_value"])]
        for item in data.get("secrets", [])
    ]
    checks = "".join(
        f"<li>{html.escape(item['label'])} — <strong>{html.escape(item['status'])}</strong></li>"
        for item in data.get("checks", [])
    )
    return f"""
    {page_header("Secret Management Audit", f"{data['secrets_total']} secret settings tracked.")}
    <div class="card"><h3>Checks</h3><ul>{checks}</ul></div>
    <div class="card"><h3>Secret Inventory</h3>{_table(["Key", "Category", "Masked Value"], rows)}</div>
    """


def build_api_keys_body() -> str:
    data = svc.api_key_rotation_status()
    rows = [
        [
            html.escape(str(row.get("key_prefix", ""))),
            html.escape(str(row.get("status", ""))),
            str(row.get("age_days", "n/a")),
            "Yes" if row.get("needs_rotation") else "No",
        ]
        for row in data.get("keys", [])[:20]
    ]
    return f"""
    {page_header("API Key Rotation", f"Policy: rotate every {data['rotation_policy_days']} days.")}
    {metric_cards([
        ("Total Keys", data.get("keys_total", 0)),
        ("Need Rotation", data.get("keys_needing_rotation", 0)),
    ])}
    <div class="card">
        <p>Rotate via API: <code>POST /api/v1/security-compliance/api-keys/&lt;id&gt;/rotate</code></p>
        <h3>Key Status</h3>{_table(["Prefix", "Status", "Age (days)", "Needs Rotation"], rows)}
    </div>
    """


def build_jwt_body() -> str:
    data = svc.jwt_audit()
    summary = data["summary"]
    rows = [
        [
            html.escape(str(item.get("user_id", ""))),
            html.escape(str(item.get("status", ""))),
            html.escape(str(item.get("expires_at", ""))),
        ]
        for item in data.get("sessions", [])[:20]
    ]
    return f"""
    {page_header("JWT Audit", "Refresh token session lifecycle.")}
    {metric_cards([
        ("Active", summary.get("active", 0)),
        ("Revoked", summary.get("revoked", 0)),
        ("Expired", summary.get("expired", 0)),
    ])}
    <div class="card"><h3>Sessions</h3>{_table(["User", "Status", "Expires"], rows)}</div>
    """


def build_rbac_body() -> str:
    data = svc.rbac_permission_matrix()
    platform_rows = [
        [html.escape(role), ", ".join(perms[:8])]
        for role, perms in sorted(data.get("platform_roles", {}).items())
    ]
    enterprise_rows = [
        [
            html.escape(str(item.get("role_code", ""))),
            ", ".join(item.get("permissions", [])[:8]),
        ]
        for item in data.get("enterprise_roles", [])
    ]
    return f"""
    {page_header("RBAC Permission Matrix", f"{data.get('role_count', 0)} roles mapped.")}
    <div class="card"><h3>Platform Roles</h3>{_table(["Role", "Permissions"], platform_rows)}</div>
    <div class="card"><h3>Enterprise Roles</h3>{_table(["Role", "Permissions"], enterprise_rows)}</div>
    """


def build_audit_body() -> str:
    data = svc.audit_log_viewer(limit=50)
    rows = [
        [
            html.escape(str(item.get("created_at", ""))),
            html.escape(str(item.get("user_email") or item.get("actor_email") or "")),
            html.escape(str(item.get("action", ""))),
            html.escape(str(item.get("object_type") or item.get("resource_type") or "")),
        ]
        for item in (data.get("platform_logs", []) + data.get("enterprise_logs", []))[:30]
    ]
    return f"""
    {page_header("Audit Log Viewer", "Platform and enterprise audit trails.")}
    {metric_cards([
        ("Platform Logs", data.get("platform_audit_count", 0)),
        ("Enterprise Logs", data.get("enterprise_audit_count", 0)),
    ])}
    <div class="card"><h3>Recent Entries</h3>{_table(["Time", "Actor", "Action", "Resource"], rows)}</div>
    """


def build_timeline_body() -> str:
    data = svc.security_event_timeline(limit=50)
    rows = [
        [
            html.escape(str(item.get("timestamp", ""))),
            html.escape(str(item.get("severity", ""))),
            html.escape(str(item.get("event_type", ""))),
            html.escape(str(item.get("message", ""))),
        ]
        for item in data.get("timeline", [])[:30]
    ]
    return f"""
    {page_header("Security Event Timeline", f"{data.get('events_total', 0)} events.")}
    <div class="card">{_table(["Time", "Severity", "Type", "Message"], rows)}</div>
    """


def build_failed_logins_body() -> str:
    data = svc.failed_login_analytics()
    rows = [
        [html.escape(ip), str(count)] for ip, count in data.get("top_source_ips", [])
    ]
    return f"""
    {page_header("Failed Login Analytics", "Access denials and authentication failures.")}
    {metric_cards([
        ("Failed Access", data.get("failed_access_attempts", 0)),
        ("Auth Audit Entries", data.get("auth_audit_entries", 0)),
        ("Security Events", data.get("security_events", 0)),
    ])}
    <div class="card"><h3>Top Source IPs</h3>{_table(["IP", "Failures"], rows)}</div>
    """


def build_ip_whitelist_body() -> str:
    data = svc.ip_whitelist_framework()
    rows = [
        [html.escape(item.get("cidr", "")), html.escape(item.get("label", "")), str(item.get("enabled"))]
        for item in data.get("rules", [])
    ]
    guidance = "".join(f"<li>{html.escape(item)}</li>" for item in data.get("pilot_guidance", []))
    return f"""
    {page_header("IP Whitelist Framework", f"Mode: {html.escape(str(data.get('enforcement_mode')))}.")}
    {metric_cards([
        ("Enabled", "Yes" if data.get("enabled") else "No"),
        ("Rules", data.get("rules_total", 0)),
    ])}
    <div class="card"><h3>Pilot Guidance</h3><ul>{guidance}</ul></div>
    <div class="card"><h3>Rules</h3>{_table(["CIDR", "Label", "Enabled"], rows)}</div>
    """


def build_rate_limits_body() -> str:
    data = svc.rate_limit_dashboard()
    exempt = "".join(f"<li><code>{html.escape(path)}</code></li>" for path in data.get("exempt_paths", []))
    headers = ", ".join(data.get("security_headers", []))
    return f"""
    {page_header("Rate Limit Dashboard", "API throttling and security headers.")}
    {metric_cards([
        ("Enabled", "Yes" if data.get("enabled") else "No"),
        ("Max Requests", data.get("max_requests", 0)),
        ("Window (sec)", data.get("window_seconds", 0)),
    ])}
    <div class="card"><h3>Security Headers</h3><p>{html.escape(headers)}</p></div>
    <div class="card"><h3>Exempt Paths</h3><ul>{exempt}</ul></div>
    """


def build_phi_access_body() -> str:
    data = svc.phi_access_audit(limit=50)
    rows = [
        [
            html.escape(str(item.get("created_at", ""))),
            html.escape(str(item.get("user_email") or "")),
            html.escape(str(item.get("action", ""))),
            html.escape(str(item.get("object_type") or item.get("resource") or "")),
        ]
        for item in (data.get("audit_logs", []) + data.get("access_history", []))[:30]
    ]
    return f"""
    {page_header("PHI Access Audit", "Protected health information access trail.")}
    {metric_cards([
        ("Audit Logs", data.get("phi_audit_entries", 0)),
        ("Access History", data.get("phi_access_entries", 0)),
    ])}
    <div class="card"><h3>Recent PHI Access</h3>{_table(["Time", "User", "Action", "Resource"], rows)}</div>
    """


def build_compliance_body() -> str:
    data = svc.compliance_report()
    return f"""
    {page_header("Compliance Report", f"Readiness score {data.get('readiness_score', 0)}%.")}
    <div class="card">
        <p>Pilot ready: <strong>{'Yes' if data.get('pilot_ready') else 'Review required'}</strong></p>
        <p>Generate readiness JSON: <code>python backend/scripts/verify_security_compliance.py</code></p>
    </div>
    <div class="card"><h3>Report Preview</h3><pre>{html.escape(json.dumps(data, indent=2, default=str)[:8000])}</pre></div>
    """
