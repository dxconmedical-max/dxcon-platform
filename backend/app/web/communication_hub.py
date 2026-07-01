from flask import Blueprint

from app.models.communication_hub import (
    CommunicationDeadLetter,
    CommunicationDeliveryTrack,
    CommunicationQueueItem,
    WebhookEndpoint,
    WorkflowAutomationEvent,
)
from app.models.notification import Notification
from app.models.notification_template import NotificationTemplate
from app.services.communication_hub_service import CommunicationHubService, NotificationCenterService


communication_hub_web_bp = Blueprint("communication_hub_web", __name__)


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
        ("/hub/notifications", "Notifications"),
        ("/events", "Events"),
        ("/templates", "Templates"),
        ("/webhooks", "Webhooks"),
    ]
    items = ""
    for href, label in links:
        cls = ' style="font-weight:bold;"' if href == active else ""
        items += f'<a href="{href}"{cls}>{label}</a>'
    return f'<div class="sidebar"><h2>Communication Hub</h2>{items}</div>'


@communication_hub_web_bp.route("/hub/notifications")
def notifications_dashboard():
    CommunicationHubService.ensure_defaults()
    summary = NotificationCenterService.hub_summary()
    rows = Notification.query.order_by(Notification.created_at.desc()).limit(20).all()
    table = ""
    for row in rows:
        table += f"<tr><td>{row.notification_code}</td><td>{row.template_code}</td><td>{row.status}</td></tr>"
    queue_rows = CommunicationQueueItem.query.order_by(CommunicationQueueItem.created_at.desc()).limit(10).all()
    queue_table = ""
    for row in queue_rows:
        queue_table += f"<tr><td>{row.queue_code}</td><td>{row.channel}</td><td>{row.status}</td><td>{row.retry_count}</td></tr>"
    return f"""
    <html><head><title>Notifications</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/hub/notifications")}<div class="content">
    <div class="card"><h1>Notification Center</h1>
    <div class="grid">
        <div class="metric"><span>Queue</span><strong>{summary["queue_size"]}</strong></div>
        <div class="metric"><span>Deliveries</span><strong>{summary["delivery_count"]}</strong></div>
        <div class="metric"><span>Dead Letter</span><strong>{summary["dead_letter_count"]}</strong></div>
        <div class="metric"><span>Webhooks</span><strong>{summary["webhook_count"]}</strong></div>
    </div>
    <p>Channels: Email, SMS, Push, Webhook</p>
    </div>
    <div class="card"><h2>Recent Notifications</h2>
    <table><tr><th>Code</th><th>Template</th><th>Status</th></tr>{table or "<tr><td colspan='3'>No notifications</td></tr>"}</table>
    </div>
    <div class="card"><h2>Queue</h2>
    <table><tr><th>Code</th><th>Channel</th><th>Status</th><th>Retries</th></tr>{queue_table or "<tr><td colspan='4'>Queue empty</td></tr>"}</table>
    </div></div></div></body></html>
    """


@communication_hub_web_bp.route("/events")
def events_dashboard():
    CommunicationHubService.ensure_defaults()
    rows = WorkflowAutomationEvent.query.order_by(WorkflowAutomationEvent.created_at.desc()).limit(20).all()
    table = ""
    for row in rows:
        table += f"<tr><td>{row.event_code}</td><td>{row.event_type}</td><td>{row.status}</td></tr>"
    return f"""
    <html><head><title>Events</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/events")}<div class="content">
    <div class="card"><h1>Workflow Events</h1>
    <p>BookingCreated, CollectorAssigned, SampleReceived, LabCompleted, ResultApproved, CriticalResult, InvoicePaid, ContractExpired</p>
    <table><tr><th>Code</th><th>Type</th><th>Status</th></tr>{table or "<tr><td colspan='3'>No events</td></tr>"}</table>
    </div></div></div></body></html>
    """


@communication_hub_web_bp.route("/templates")
def templates_dashboard():
    CommunicationHubService.ensure_defaults()
    rows = NotificationTemplate.query.filter(NotificationTemplate.template_code.like("HUB-%")).limit(20).all()
    table = ""
    for row in rows:
        table += f"<tr><td>{row.template_code}</td><td>{row.name}</td><td>{row.default_channels}</td></tr>"
    return f"""
    <html><head><title>Templates</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/templates")}<div class="content">
    <div class="card"><h1>Message Templates</h1>
    <p>Email, SMS, and Push templates</p>
    <table><tr><th>Code</th><th>Name</th><th>Channels</th></tr>{table or "<tr><td colspan='3'>No templates</td></tr>"}</table>
    </div></div></div></body></html>
    """


@communication_hub_web_bp.route("/webhooks")
def webhooks_dashboard():
    CommunicationHubService.ensure_defaults()
    rows = WebhookEndpoint.query.limit(20).all()
    table = ""
    for row in rows:
        table += f"<tr><td>{row.webhook_code}</td><td>{row.name}</td><td>{row.target_url}</td><td>{'Active' if row.is_active else 'Inactive'}</td></tr>"
    deliveries = CommunicationDeliveryTrack.query.filter_by(channel="WEBHOOK").count()
    return f"""
    <html><head><title>Webhooks</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/webhooks")}<div class="content">
    <div class="card"><h1>Webhook Endpoints</h1>
    <p>Webhook deliveries tracked: {deliveries}</p>
    <table><tr><th>Code</th><th>Name</th><th>URL</th><th>Status</th></tr>{table or "<tr><td colspan='4'>No webhooks</td></tr>"}</table>
    </div></div></div></body></html>
    """
