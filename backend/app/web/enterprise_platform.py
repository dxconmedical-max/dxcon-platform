from flask import Blueprint

from app.models.enterprise_platform import (
    EnterpriseAuditRecord,
    EnterpriseFeatureFlag,
    EnterpriseLicense,
    EnterpriseSecurityEvent,
    EnterpriseTenant,
)
from app.services.enterprise_platform_service import (
    AdminEnterpriseService,
    EnterprisePlatformService,
    MonitoringEnterpriseService,
    OrganizationEnterpriseService,
    SecurityEnterpriseService,
)


enterprise_web_bp = Blueprint("enterprise_web", __name__)


def _styles():
    return """
    body { margin:0; font-family:Arial,sans-serif; background:#f8fafc; color:#0f172a; }
    .layout { display:flex; min-height:100vh; }
    .sidebar { width:220px; background:#1e293b; color:white; padding:24px; }
    .sidebar a { display:block; color:white; text-decoration:none; padding:12px 0; border-bottom:1px solid rgba(255,255,255,.12); }
    .content { flex:1; padding:32px; }
    .card { background:white; border-radius:12px; padding:24px; box-shadow:0 4px 12px rgba(0,0,0,.08); margin-bottom:24px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:16px; }
    .metric { background:#e0f2fe; border-radius:12px; padding:16px; }
    .metric strong { display:block; font-size:24px; }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:12px; border-bottom:1px solid #e5e7eb; text-align:left; font-size:14px; }
    th { background:#e2e8f0; }
    """


def _sidebar(active):
    links = [
        ("/admin", "Admin"),
        ("/security", "Security"),
        ("/license", "License"),
        ("/tenants", "Tenants"),
        ("/system", "System"),
    ]
    items = ""
    for href, label in links:
        cls = ' style="font-weight:bold;"' if href == active else ""
        items += f'<a href="{href}"{cls}>{label}</a>'
    return f'<div class="sidebar"><h2>Enterprise</h2>{items}</div>'


@enterprise_web_bp.route("/admin")
def admin_dashboard():
    EnterprisePlatformService.ensure_defaults()
    overview = AdminEnterpriseService.overview()
    return f"""
    <html><head><title>Enterprise Admin</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/admin")}<div class="content">
    <div class="card"><h1>Enterprise Administration</h1>
    <div class="grid">
        <div class="metric"><span>Tenants</span><strong>{overview["tenants"]}</strong></div>
        <div class="metric"><span>Organizations</span><strong>{overview["organizations"]}</strong></div>
        <div class="metric"><span>Licenses</span><strong>{overview["licenses"]}</strong></div>
        <div class="metric"><span>Audit Records</span><strong>{overview["audit_records"]}</strong></div>
    </div>
    </div></div></div></body></html>
    """


@enterprise_web_bp.route("/security")
def security_dashboard():
    EnterprisePlatformService.ensure_defaults()
    roles = SecurityEnterpriseService.list_rbac_roles()
    policies = SecurityEnterpriseService.list_abac_policies()
    providers = SecurityEnterpriseService.list_identity_providers()
    return f"""
    <html><head><title>Security</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/security")}<div class="content">
    <div class="card"><h1>Enterprise Security</h1>
    <div class="grid">
        <div class="metric"><span>RBAC Roles</span><strong>{roles["count"]}</strong></div>
        <div class="metric"><span>ABAC Policies</span><strong>{policies["count"]}</strong></div>
        <div class="metric"><span>Identity Providers</span><strong>{providers["count"]}</strong></div>
        <div class="metric"><span>Security Events</span><strong>{EnterpriseSecurityEvent.query.count()}</strong></div>
    </div>
    <p>OIDC, OAuth2, SAML supported</p>
    </div></div></div></body></html>
    """


@enterprise_web_bp.route("/license")
def license_dashboard():
    EnterprisePlatformService.ensure_defaults()
    rows = EnterpriseLicense.query.limit(20).all()
    table = ""
    for row in rows:
        table += f"<tr><td>{row.license_key[:16]}...</td><td>{row.plan_code}</td><td>{row.status}</td><td>{row.seat_limit}</td></tr>"
    return f"""
    <html><head><title>License</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/license")}<div class="content">
    <div class="card"><h1>License Management</h1>
    <table><tr><th>Key</th><th>Plan</th><th>Status</th><th>Seats</th></tr>{table or "<tr><td colspan='4'>No licenses</td></tr>"}</table>
    </div></div></div></body></html>
    """


@enterprise_web_bp.route("/tenants")
def tenants_dashboard():
    EnterprisePlatformService.ensure_defaults()
    rows = EnterpriseTenant.query.limit(20).all()
    table = ""
    for row in rows:
        table += f"<tr><td>{row.tenant_code}</td><td>{row.name}</td><td>{row.isolation_mode}</td><td>{row.status}</td></tr>"
    orgs = OrganizationEnterpriseService.list_organizations()
    return f"""
    <html><head><title>Tenants</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/tenants")}<div class="content">
    <div class="card"><h1>Multi-Tenant Management</h1>
    <p>Organizations: {orgs["count"]}</p>
    <table><tr><th>Code</th><th>Name</th><th>Isolation</th><th>Status</th></tr>{table or "<tr><td colspan='4'>No tenants</td></tr>"}</table>
    </div></div></div></body></html>
    """


@enterprise_web_bp.route("/system")
def system_dashboard():
    EnterprisePlatformService.ensure_defaults()
    health = MonitoringEnterpriseService.health()
    metrics = MonitoringEnterpriseService.metrics()
    flags = EnterpriseFeatureFlag.query.limit(10).all()
    flag_rows = ""
    for row in flags:
        flag_rows += f"<tr><td>{row.flag_code}</td><td>{row.name}</td><td>{'ON' if row.enabled else 'OFF'}</td></tr>"
    return f"""
    <html><head><title>System</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/system")}<div class="content">
    <div class="card"><h1>System Settings & Monitoring</h1>
    <div class="grid">
        <div class="metric"><span>Health</span><strong>{health["status"]}</strong></div>
        <div class="metric"><span>Pending Jobs</span><strong>{metrics["pending_jobs"]}</strong></div>
        <div class="metric"><span>Audit Records</span><strong>{metrics["audit_records"]}</strong></div>
        <div class="metric"><span>Feature Flags</span><strong>{EnterpriseFeatureFlag.query.count()}</strong></div>
    </div>
    </div>
    <div class="card"><h2>Feature Flags</h2>
    <table><tr><th>Code</th><th>Name</th><th>Status</th></tr>{flag_rows or "<tr><td colspan='3'>No flags</td></tr>"}</table>
    </div></div></div></body></html>
    """
