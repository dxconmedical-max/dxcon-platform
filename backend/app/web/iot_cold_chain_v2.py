from flask import Blueprint, redirect

from app.services.iot_cold_chain_service import (
    ColdChainAlertService,
    ColdChainService,
    IoTDeviceService,
)


iot_web_bp = Blueprint("iot_web", __name__)


def _styles():
    return """
    body { margin:0; font-family:Arial,sans-serif; background:#f8fafc; color:#0f172a; }
    .layout { display:flex; min-height:100vh; }
    .sidebar { width:220px; background:#1d4ed8; color:white; padding:24px; }
    .sidebar a { display:block; color:white; text-decoration:none; padding:12px 0; border-bottom:1px solid rgba(255,255,255,.12); }
    .content { flex:1; padding:32px; }
    .card { background:white; border-radius:12px; padding:24px; box-shadow:0 4px 12px rgba(0,0,0,.08); margin-bottom:24px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:16px; }
    .metric { background:#dbeafe; border-radius:12px; padding:16px; }
    .metric strong { display:block; font-size:24px; }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:12px; border-bottom:1px solid #e5e7eb; text-align:left; font-size:14px; }
    th { background:#e2e8f0; }
    """


def _sidebar(active):
    links = [
        ("/iot/devices", "Devices"),
        ("/iot/cold-chain", "Cold Chain"),
        ("/iot/alerts", "Alerts"),
    ]
    items = ""
    for href, label in links:
        style = ' style="font-weight:bold;"' if href == active else ""
        items += f'<a href="{href}"{style}>{label}</a>'
    return f'<div class="sidebar"><h2>IoT</h2>{items}</div>'


@iot_web_bp.route("/iot")
def iot_home():
    return redirect("/iot/devices")


@iot_web_bp.route("/iot/devices")
def iot_devices_page():
    devices = IoTDeviceService.list_devices()
    rows = ""
    for item in devices.get("devices", [])[:25]:
        cold_box = item.get("cold_box") or {}
        rows += f"<tr><td>{item.get('device_code', '')}</td><td>{cold_box.get('box_code', '')}</td><td>{item.get('status', '')}</td><td>{item.get('last_seen_at', '')}</td></tr>"
    return f"""
    <html><head><title>IoT Devices</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/iot/devices")}<div class="content">
    <div class="card"><h1>Devices</h1>
    <table><tr><th>Device</th><th>Box</th><th>Status</th><th>Last Seen</th></tr>{rows or "<tr><td colspan='4'>No devices</td></tr>"}</table>
    </div></div></div></body></html>
    """


@iot_web_bp.route("/iot/cold-chain")
def iot_cold_chain_page():
    status = ColdChainService.get_status()
    summary = status.get("summary", {})
    rows = ""
    for item in status.get("devices", [])[:25]:
        device = item.get("device") or {}
        temp = item.get("latest_temperature") or {}
        rows += f"<tr><td>{device.get('device_code', '')}</td><td>{temp.get('celsius', '')}</td><td>{item.get('in_range', '')}</td><td>{item.get('open_alerts', 0)}</td></tr>"
    return f"""
    <html><head><title>Cold Chain</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/iot/cold-chain")}<div class="content">
    <div class="card"><h1>Cold Chain Status</h1>
    <div class="grid">
        <div class="metric"><span>Devices</span><strong>{summary.get('devices_total', 0)}</strong></div>
        <div class="metric"><span>In Range</span><strong>{summary.get('devices_in_range', 0)}</strong></div>
        <div class="metric"><span>Open Alerts</span><strong>{summary.get('open_alerts_total', 0)}</strong></div>
    </div>
    <table><tr><th>Device</th><th>Temp (C)</th><th>In Range</th><th>Alerts</th></tr>{rows or "<tr><td colspan='4'>No cold chain data</td></tr>"}</table>
    </div></div></div></body></html>
    """


@iot_web_bp.route("/iot/alerts")
def iot_alerts_page():
    alerts = ColdChainAlertService.list_alerts()
    rows = ""
    for item in alerts.get("alerts", [])[:25]:
        rows += f"<tr><td>{item.get('alert_code', '')}</td><td>{item.get('alert_type', '')}</td><td>{item.get('severity', '')}</td><td>{item.get('status', '')}</td></tr>"
    return f"""
    <html><head><title>IoT Alerts</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/iot/alerts")}<div class="content">
    <div class="card"><h1>Alerts</h1>
    <table><tr><th>Code</th><th>Type</th><th>Severity</th><th>Status</th></tr>{rows or "<tr><td colspan='4'>No alerts</td></tr>"}</table>
    </div></div></div></body></html>
    """
