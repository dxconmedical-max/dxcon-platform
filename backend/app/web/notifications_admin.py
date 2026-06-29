from flask import Blueprint

from app.services.notification_service import NotificationService


notifications_admin_web_bp = Blueprint("notifications_admin_web", __name__)


def _styles():
    return """
    body { margin:0; font-family:Arial,sans-serif; background:#f8fafc; color:#0f172a; }
    .layout { max-width:1100px; margin:0 auto; padding:32px; }
    .nav a { margin-right:16px; }
    .card { background:white; border-radius:12px; padding:24px; box-shadow:0 4px 12px rgba(0,0,0,.08); margin-bottom:24px; }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:12px; border-bottom:1px solid #e5e7eb; text-align:left; font-size:14px; }
    th { background:#e2e8f0; }
    .badge { padding:4px 8px; border-radius:999px; background:#dbeafe; font-size:12px; }
    """


def _nav(active):
    links = [
        ("/notifications", "Notifications"),
        ("/notification-templates", "Templates"),
    ]
    items = ""
    for href, label in links:
        style = ' style="font-weight:bold;"' if href == active else ""
        items += f'<a href="{href}"{style}>{label}</a>'
    return f'<div class="nav">{items}</div>'


@notifications_admin_web_bp.route("/notifications")
def notifications_home():
    notifications = NotificationService.list_notifications()
    rows = ""
    for item in notifications[:50]:
        rows += f"""
        <tr>
            <td>{item.notification_code}</td>
            <td>{item.template_code}</td>
            <td>{item.subject or ""}</td>
            <td><span class="badge">{item.status}</span></td>
            <td>{item.created_at}</td>
        </tr>
        """

    return f"""
    <html><head><title>Notifications</title><style>{_styles()}</style></head><body>
    <div class="layout">
    <div class="card"><h1>Notification Center</h1>{_nav("/notifications")}</div>
    <div class="card">
    <table><tr><th>Code</th><th>Template</th><th>Subject</th><th>Status</th><th>Created</th></tr>
    {rows or "<tr><td colspan='5'>No notifications yet</td></tr>"}
    </table>
    </div>
    </div></body></html>
    """


@notifications_admin_web_bp.route("/notification-templates")
def notification_templates_home():
    templates = NotificationService.list_templates()
    rows = ""
    for template in templates:
        rows += f"""
        <tr>
            <td>{template.template_code}</td>
            <td>{template.name}</td>
            <td>{template.subject or ""}</td>
            <td>{template.default_channels}</td>
            <td>{template.status}</td>
        </tr>
        """

    return f"""
    <html><head><title>Notification Templates</title><style>{_styles()}</style></head><body>
    <div class="layout">
    <div class="card"><h1>Notification Templates</h1>{_nav("/notification-templates")}</div>
    <div class="card">
    <table><tr><th>Code</th><th>Name</th><th>Subject</th><th>Channels</th><th>Status</th></tr>
    {rows or "<tr><td colspan='5'>No templates</td></tr>"}
    </table>
    </div>
    </div></body></html>
    """
