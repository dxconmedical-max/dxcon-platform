"""IoT Cold Chain Logistics web rendering helpers."""

from __future__ import annotations

import json

from flask import session

from app.services import iot_logistics_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

LOGISTICS_NAV = (
    ("Dashboard", "/iot-logistics"),
    ("Devices", "/iot-logistics/devices"),
    ("Cold Boxes", "/iot-logistics/cold-boxes"),
    ("Adapters", "/iot-logistics/adapters"),
    ("Alerts", "/iot-logistics/alerts"),
    ("Timeline", "/iot-logistics/timeline"),
    ("Chain of Custody", "/iot-logistics/chain-of-custody"),
    ("Offline Buffer", "/iot-logistics/offline-buffer"),
    ("Device Health", "/iot-logistics/device-health"),
    ("Ingest", "/iot-logistics/ingest"),
)


def logistics_styles() -> str:
    return pilot_styles() + """
    .btn { background:#0369a1; color:white; border:none; padding:8px 14px; border-radius:8px; cursor:pointer; text-decoration:none; font-size:13px; }
    .form-grid label { display:block; font-size:13px; color:#475569; margin-bottom:4px; }
    .form-grid input, .form-grid select, .form-grid textarea { width:100%; max-width:520px; padding:10px; border:1px solid #cbd5e1; border-radius:8px; margin-bottom:12px; }
    .error { background:#fef2f2; border:1px solid #fecaca; color:#991b1b; padding:12px 16px; border-radius:10px; margin-bottom:16px; }
    .feature-list { columns:2; gap:24px; font-size:13px; color:#334155; }
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; max-width:100%; }
    """


def render_logistics_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in LOGISTICS_NAV)
    actor = session.get("email", "Logistics")
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{logistics_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted" style="margin-bottom:14px;">Signed in as {actor} · Phase 4 Sprint 4.3</div>
            {body_html}
        </div>
    </body>
    </html>
    """


def _table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "<p class='muted'>No records.</p>"
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
    return f"<table><tr>{head}</tr>{body}</table>"


def build_dashboard_body() -> str:
    data = svc.dashboard_payload()
    summary = data["summary"]
    cards = metric_cards(
        [
            ("Devices", summary["devices"]),
            ("Cold Boxes", summary["cold_boxes"]),
            ("Open Alerts", summary["open_alerts"]),
            ("Offline Buffered", summary["offline_buffered"]),
            ("In Range", summary["devices_in_range"]),
            ("Adapters", summary["adapters"]),
        ]
    )
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    return f"""
    {page_header("Logistics IoT Dashboard", "Track sample transport with GPS, temperature, and shock telemetry.")}
    {cards}
    <div class="card" style="margin-top:20px;">
        <h3>Sprint 4.3 Features</h3>
        <ul class="feature-list">{features}</ul>
    </div>
    """


def build_devices_body() -> str:
    data = svc.list_devices()
    rows = [
        [item.get("device_code", ""), item.get("device_type", ""), item.get("status", ""), item.get("last_seen_at", "")]
        for item in data.get("devices", [])
    ]
    return f"""
    {page_header("IoT Device Registry", f"{data['count']} devices registered.")}
    {_table(["Code", "Type", "Status", "Last Seen"], rows)}
    """


def build_cold_boxes_body() -> str:
    data = svc.list_cold_boxes()
    rows = [
        [
            row.get("box_code", ""),
            str(row.get("min_temp_c", "")),
            str(row.get("max_temp_c", "")),
            row.get("status", ""),
        ]
        for row in data.get("cold_boxes", [])
    ]
    return f"""
    {page_header("Cold Box Registry", f"{data['count']} cold boxes.")}
    {_table(["Box", "Min C", "Max C", "Status"], rows)}
    """


def build_adapters_body() -> str:
    data = svc.list_adapters()
    rows = [[row.get("type", ""), row.get("vendor", "")] for row in data.get("adapters", [])]
    return f"""
    {page_header("Device Adapters", f"{data['count']} adapter types.")}
    {_table(["Type", "Vendor"], rows)}
    """


def build_alerts_body() -> str:
    data = svc.list_sensor_alerts()
    rows = [
        [row.get("alert_code", ""), row.get("alert_type", ""), row.get("severity", ""), row.get("status", "")]
        for row in data.get("alerts", [])
    ]
    return f"""
    {page_header("Sensor Alerts", f"{data['count']} alerts.")}
    {_table(["Code", "Type", "Severity", "Status"], rows)}
    """


def build_timeline_body(device_id: str = "") -> str:
    timeline_html = "<p class='muted'>Provide device_id query param to load route timeline.</p>"
    if device_id:
        data = svc.route_timeline(device_id)
        rows = [
            [item.get("kind", ""), item.get("timestamp", ""), json.dumps(item.get("payload", {}))[:80]]
            for item in data.get("timeline", [])
        ]
        timeline_html = _table(["Kind", "Timestamp", "Payload"], rows)
    return f"""
    {page_header("Route Timeline", "Chronological GPS, temperature, shock, and custody events.")}
    <form method="GET" class="form-grid card">
        <label for="device_id">Device ID</label>
        <input id="device_id" name="device_id" value="{device_id}" />
        <button class="btn" type="submit">Load Timeline</button>
    </form>
    {timeline_html}
    """


def build_chain_of_custody_body() -> str:
    data = svc.list_chain_of_custody(limit=50)
    rows = [
        [row.get("event_code", ""), row.get("event_type", ""), row.get("reference_id", ""), row.get("created_at", "")]
        for row in data.get("events", [])
    ]
    return f"""
    {page_header("Chain of Custody", f"{data['count']} custody events.")}
    {_table(["Code", "Type", "Device", "Created"], rows)}
    """


def build_offline_buffer_body() -> str:
    data = svc.list_offline_buffer()
    rows = [
        [row.get("device_id", "")[:8], row.get("event_type", ""), row.get("adapter_type", ""), row.get("status", "")]
        for row in data.get("events", [])
    ]
    return f"""
    {page_header("Offline Device Event Buffer", f"{data['pending']} pending events.")}
    {_table(["Device", "Event", "Adapter", "Status"], rows)}
    """


def build_device_health_body(device_id: str = "") -> str:
    body = "<p class='muted'>Provide device_id query param to inspect device health.</p>"
    if device_id:
        health = svc.device_health(device_id)
        body = f"""
        <div class="card">
            <p><strong>Connectivity:</strong> {health.get('connectivity')}</p>
            <p><strong>Health Score:</strong> {health.get('health_score')}</p>
            <p><strong>Battery:</strong> {health.get('battery_percent')}</p>
            <p><strong>Open Alerts:</strong> {health.get('open_alerts')}</p>
            <p><strong>Pending Offline Events:</strong> {health.get('pending_offline_events')}</p>
        </div>
        """
    return f"""
    {page_header("Device Health", "Connectivity, battery, alerts, and buffer status.")}
    <form method="GET" class="form-grid card">
        <label for="device_id">Device ID</label>
        <input id="device_id" name="device_id" value="{device_id}" />
        <button class="btn" type="submit">Check Health</button>
    </form>
    {body}
    """


def build_ingest_form_body(*, result: dict | None = None, error: str = "") -> str:
    flash = f'<div class="error">{error}</div>' if error else ""
    result_html = ""
    if result:
        result_html = f"<h3>Ingest Result</h3><pre>{json.dumps(result, indent=2, default=str)}</pre>"
    return f"""
    {flash}
    {page_header("Device Ingestion API", "Adapter-based ingestion for temperature, GPS, and shock events.")}
    <form method="POST" class="form-grid card">
        <label for="adapter_type">Adapter Type</label>
        <select id="adapter_type" name="adapter_type">
            <option value="GENERIC">GENERIC</option>
            <option value="DEMO_SENSOR">DEMO_SENSOR</option>
            <option value="VENDOR_GATEWAY">VENDOR_GATEWAY</option>
        </select>
        <label for="payload">Payload JSON</label>
        <textarea id="payload" name="payload" rows="8">{{"event_type":"TEMPERATURE","device_id":"DEVICE-ID","celsius":5.5}}</textarea>
        <button class="btn" type="submit">Ingest Event</button>
    </form>
    {result_html}
    """
