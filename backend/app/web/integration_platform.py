from flask import Blueprint

from app.integrations.adapter_manager import AdapterManager
from app.models.integration_platform import IntegrationDeadLetter, IntegrationDomainEvent, IntegrationJob, WebhookDelivery, WebhookEndpoint
from app.plugins.plugin_manager import PluginManager
from app.services.integration_platform_service import IntegrationPlatformService, SandboxService


integration_platform_web_bp = Blueprint("integration_platform_web", __name__)


def _styles():
    return """
    <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f4f6f8; color: #1f2933; }
    .layout { display: flex; min-height: 100vh; }
    .sidebar { width: 240px; background: #102a43; color: #fff; padding: 20px; }
    .sidebar a { color: #d9e2ec; display: block; margin: 8px 0; text-decoration: none; }
    .sidebar a.active { color: #fff; font-weight: bold; }
    .content { flex: 1; padding: 24px; }
    table { width: 100%; border-collapse: collapse; background: #fff; }
    th, td { border: 1px solid #d9e2ec; padding: 8px; text-align: left; }
    .card { background: #fff; padding: 16px; margin-bottom: 16px; border: 1px solid #d9e2ec; }
    </style>
    """


def _sidebar(active):
    links = [
        ("/integrations/platform", "Platform"),
        ("/integrations/adapters", "Adapters"),
        ("/integrations/plugins", "Plugins"),
        ("/integrations/events", "Events"),
        ("/integrations/webhooks", "Webhooks"),
        ("/integrations/queue", "Queue"),
        ("/integrations/sandbox", "Sandbox"),
    ]
    items = "".join(
        f'<a href="{href}" class="{"active" if href == active else ""}">{label}</a>' for href, label in links
    )
    return f'<div class="sidebar"><h2>Integration Platform</h2>{items}</div>'


@integration_platform_web_bp.route("/integrations/platform")
def platform_dashboard():
    IntegrationPlatformService.ensure_defaults()
    status = SandboxService.status()
    return f"""<!DOCTYPE html><html><head><title>Integration Platform</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/integrations/platform")}<div class="content">
    <h1>Integration Platform Core</h1>
    <div class="card"><strong>Status:</strong> {status["status"]}<br>
    <strong>Adapters:</strong> {status["adapters"]}<br>
    <strong>Plugins:</strong> {status["plugins"]}<br>
    <strong>Supported Events:</strong> {len(status["supported_events"])}</div>
    </div></div></body></html>"""


@integration_platform_web_bp.route("/integrations/adapters")
def adapters_dashboard():
    AdapterManager.initialize()
    rows = AdapterManager.list_adapters()["adapters"]
    table = "".join(
        f"<tr><td>{row['type']}</td><td>{row['vendor']}</td><td>{'Connected' if row['connected'] else 'Disconnected'}</td></tr>"
        for row in rows
    )
    return f"""<!DOCTYPE html><html><head><title>Adapters</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/integrations/adapters")}<div class="content">
    <h1>Adapter Framework</h1>
    <table><tr><th>Type</th><th>Vendor</th><th>State</th></tr>{table}</table>
    </div></div></body></html>"""


@integration_platform_web_bp.route("/integrations/plugins")
def plugins_dashboard():
    PluginManager.ensure_defaults()
    rows = PluginManager.list_plugins()["plugins"]
    table = "".join(
        f"<tr><td>{row['plugin_id']}</td><td>{row['name']}</td><td>{row['status']}</td></tr>" for row in rows
    )
    return f"""<!DOCTYPE html><html><head><title>Plugins</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/integrations/plugins")}<div class="content">
    <h1>Plugin Framework</h1>
    <table><tr><th>ID</th><th>Name</th><th>Status</th></tr>{table or "<tr><td colspan='3'>No plugins</td></tr>"}</table>
    </div></div></body></html>"""


@integration_platform_web_bp.route("/integrations/events")
def events_dashboard():
    IntegrationPlatformService.ensure_defaults()
    rows = IntegrationDomainEvent.query.order_by(IntegrationDomainEvent.created_at.desc()).limit(20).all()
    table = "".join(
        f"<tr><td>{row.event_code}</td><td>{row.event_type}</td><td>{row.status}</td></tr>" for row in rows
    )
    return f"""<!DOCTYPE html><html><head><title>Events</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/integrations/events")}<div class="content">
    <h1>Domain Event Bus</h1>
    <table><tr><th>Code</th><th>Type</th><th>Status</th></tr>{table or "<tr><td colspan='3'>No events</td></tr>"}</table>
    </div></div></body></html>"""


@integration_platform_web_bp.route("/integrations/webhooks")
def webhooks_dashboard():
    IntegrationPlatformService.ensure_defaults()
    rows = WebhookEndpoint.query.order_by(WebhookEndpoint.created_at.desc()).all()
    table = "".join(
        f"<tr><td>{row.endpoint_code}</td><td>{row.name}</td><td>{row.target_url}</td><td>{row.status}</td></tr>"
        for row in rows
    )
    deliveries = WebhookDelivery.query.count()
    return f"""<!DOCTYPE html><html><head><title>Webhooks</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/integrations/webhooks")}<div class="content">
    <h1>Webhook Engine</h1>
    <div class="card">Deliveries logged: {deliveries}</div>
    <table><tr><th>Code</th><th>Name</th><th>URL</th><th>Status</th></tr>{table or "<tr><td colspan='4'>No webhooks</td></tr>"}</table>
    </div></div></body></html>"""


@integration_platform_web_bp.route("/integrations/queue")
def queue_dashboard():
    IntegrationPlatformService.ensure_defaults()
    jobs = IntegrationJob.query.order_by(IntegrationJob.created_at.desc()).limit(20).all()
    dead = IntegrationDeadLetter.query.count()
    table = "".join(
        f"<tr><td>{row.job_code}</td><td>{row.adapter_type}</td><td>{row.status}</td></tr>" for row in jobs
    )
    return f"""<!DOCTYPE html><html><head><title>Queue</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/integrations/queue")}<div class="content">
    <h1>Integration Queue</h1>
    <div class="card">Dead letters: {dead}</div>
    <table><tr><th>Code</th><th>Adapter</th><th>Status</th></tr>{table or "<tr><td colspan='3'>No jobs</td></tr>"}</table>
    </div></div></body></html>"""


@integration_platform_web_bp.route("/integrations/sandbox")
def sandbox_dashboard():
    status = SandboxService.status()
    return f"""<!DOCTYPE html><html><head><title>Sandbox</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/integrations/sandbox")}<div class="content">
    <h1>Integration Sandbox</h1>
    <div class="card">
    <p>Use API endpoints under <code>/api/v1/sandbox/*</code> to simulate external systems.</p>
    <p>Status: {status["status"]}</p>
    <p>Adapters available: {status["adapters"]}</p>
    </div>
    </div></div></body></html>"""
