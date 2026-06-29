from flask import Blueprint, redirect

from app.services.integration_service import IntegrationGatewayService


integrations_web_bp = Blueprint("integrations_web", __name__)


def _styles():
    return """
    body { margin:0; font-family:Arial,sans-serif; background:#f8fafc; color:#0f172a; }
    .layout { display:flex; min-height:100vh; }
    .sidebar { width:220px; background:#0f766e; color:white; padding:24px; }
    .sidebar a { display:block; color:white; text-decoration:none; padding:12px 0; border-bottom:1px solid rgba(255,255,255,.12); }
    .content { flex:1; padding:32px; }
    .card { background:white; border-radius:12px; padding:24px; box-shadow:0 4px 12px rgba(0,0,0,.08); margin-bottom:24px; }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:12px; border-bottom:1px solid #e5e7eb; text-align:left; font-size:14px; }
    th { background:#e2e8f0; }
    """


def _sidebar(active):
    links = [
        ("/integrations/connections", "Connections"),
        ("/integrations/messages", "Messages"),
    ]
    items = ""
    for href, label in links:
        style = ' style="font-weight:bold;"' if href == active else ""
        items += f'<a href="{href}"{style}>{label}</a>'
    return f'<div class="sidebar"><h2>Integrations</h2>{items}</div>'


@integrations_web_bp.route("/integrations")
def integrations_home():
    return redirect("/integrations/connections")


@integrations_web_bp.route("/integrations/connections")
def integrations_connections_page():
    connections = IntegrationGatewayService.list_connections()
    rows = ""
    for item in connections.get("connections", [])[:25]:
        partner = item.get("partner") or {}
        rows += f"<tr><td>{item.get('connection_code', '')}</td><td>{partner.get('partner_name', '')}</td><td>{item.get('protocol', '')}</td><td>{item.get('status', '')}</td></tr>"
    return f"""
    <html><head><title>Integration Connections</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/integrations/connections")}<div class="content">
    <div class="card"><h1>Connections</h1>
    <table><tr><th>Code</th><th>Partner</th><th>Protocol</th><th>Status</th></tr>{rows or "<tr><td colspan='4'>No connections</td></tr>"}</table>
    </div></div></div></body></html>
    """


@integrations_web_bp.route("/integrations/messages")
def integrations_messages_page():
    messages = IntegrationGatewayService.list_messages()
    rows = ""
    for item in messages.get("messages", [])[:25]:
        rows += f"<tr><td>{item.get('message_code', '')}</td><td>{item.get('message_type', '')}</td><td>{item.get('status', '')}</td><td>{item.get('created_at', '')}</td></tr>"
    return f"""
    <html><head><title>Integration Messages</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/integrations/messages")}<div class="content">
    <div class="card"><h1>Messages</h1>
    <table><tr><th>Code</th><th>Type</th><th>Status</th><th>Created</th></tr>{rows or "<tr><td colspan='4'>No messages</td></tr>"}</table>
    </div></div></div></body></html>
    """
