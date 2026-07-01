from flask import Blueprint

from app.models.notification_center import NCNotification, NCNotificationProvider, NCNotificationTemplate
from app.notifications.notification_service import NotificationCenterService


notification_center_web_bp = Blueprint("notification_center_web", __name__)


def _styles():
    return """
    <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f4f6f8; color: #1f2933; }
    .layout { display: flex; min-height: 100vh; }
    .sidebar { width: 240px; background: #1b4332; color: #fff; padding: 20px; }
    .sidebar a { color: #b7e4c7; display: block; margin: 8px 0; text-decoration: none; }
    .sidebar a.active { color: #fff; font-weight: bold; }
    .content { flex: 1; padding: 24px; }
    table { width: 100%; border-collapse: collapse; background: #fff; }
    th, td { border: 1px solid #d9e2ec; padding: 8px; text-align: left; }
    .card { background: #fff; padding: 16px; margin-bottom: 16px; border: 1px solid #d9e2ec; }
    </style>
    """


def _sidebar(active):
    links = [
        ("/notifications", "Overview"),
        ("/notifications/history", "History"),
        ("/notifications/providers", "Providers"),
        ("/notifications/templates", "Templates"),
        ("/notifications/statistics", "Statistics"),
    ]
    items = "".join(
        f'<a href="{href}" class="{"active" if href == active else ""}">{label}</a>' for href, label in links
    )
    return f'<div class="sidebar"><h2>Notification Center</h2>{items}</div>'


@notification_center_web_bp.route("/notifications")
def notifications_home():
    NotificationCenterService.ensure_defaults()
    stats = NotificationCenterService.statistics()
    return f"""<!DOCTYPE html><html><head><title>Notifications</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/notifications")}<div class="content">
    <h1>Notification & Communication Center</h1>
    <div class="card">Total: {stats["total"]} | Sent: {stats["sent"]} | Failed: {stats["failed"]} | Success rate: {stats["delivery_success_rate"]}%</div>
    </div></div></body></html>"""


@notification_center_web_bp.route("/notifications/history")
def notifications_history():
    rows = NCNotification.query.order_by(NCNotification.created_at.desc()).limit(30).all()
    table = "".join(
        f"<tr><td>{row.notification_code}</td><td>{row.channel}</td><td>{row.status}</td><td>{row.recipient}</td></tr>"
        for row in rows
    )
    return f"""<!DOCTYPE html><html><head><title>History</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/notifications/history")}<div class="content">
    <h1>Notification History</h1>
    <table><tr><th>Code</th><th>Channel</th><th>Status</th><th>Recipient</th></tr>{table or "<tr><td colspan='4'>No notifications</td></tr>"}</table>
    </div></div></body></html>"""


@notification_center_web_bp.route("/notifications/providers")
def notifications_providers():
    providers = NotificationCenterService.list_providers()["providers"]
    table = "".join(
        f"<tr><td>{row['provider_code']}</td><td>{row['channel']}</td><td>{row['health_status']}</td></tr>"
        for row in providers
    )
    return f"""<!DOCTYPE html><html><head><title>Providers</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/notifications/providers")}<div class="content">
    <h1>Notification Providers</h1>
    <table><tr><th>Code</th><th>Channel</th><th>Health</th></tr>{table}</table>
    </div></div></body></html>"""


@notification_center_web_bp.route("/notifications/templates")
def notifications_templates():
    rows = NCNotificationTemplate.query.order_by(NCNotificationTemplate.template_code.asc()).limit(30).all()
    table = "".join(
        f"<tr><td>{row.template_code}</td><td>{row.channel}</td><td>{row.language}</td><td>{row.name}</td></tr>"
        for row in rows
    )
    return f"""<!DOCTYPE html><html><head><title>Templates</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/notifications/templates")}<div class="content">
    <h1>Notification Templates</h1>
    <table><tr><th>Code</th><th>Channel</th><th>Language</th><th>Name</th></tr>{table or "<tr><td colspan='4'>No templates</td></tr>"}</table>
    </div></div></body></html>"""


@notification_center_web_bp.route("/notifications/statistics")
def notifications_statistics():
    stats = NotificationCenterService.statistics()
    return f"""<!DOCTYPE html><html><head><title>Statistics</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/notifications/statistics")}<div class="content">
    <h1>Notification Statistics</h1>
    <div class="card">
    Queued: {stats["queued"]}<br>
    Processing: {stats["processing"]}<br>
    Sent: {stats["sent"]}<br>
    Failed: {stats["failed"]}<br>
    Retry: {stats["retry"]}<br>
    Average latency: {stats["average_latency_ms"]} ms<br>
    Delivery success rate: {stats["delivery_success_rate"]}%
    </div></div></div></body></html>"""
