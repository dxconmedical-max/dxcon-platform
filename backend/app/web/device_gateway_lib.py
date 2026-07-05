"""Device Gateway web rendering helpers — Phase 7.5."""

from __future__ import annotations

import html
import json

from app.services import device_gateway_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

NAV = (
    ("Overview", "/device-gateway"),
    ("Gateway Registry", "/device-gateway/registry"),
    ("ASTM Adapter", "/device-gateway/astm"),
    ("HL7 Adapter", "/device-gateway/hl7"),
    ("TCP Adapter", "/device-gateway/tcp"),
    ("Serial Adapter", "/device-gateway/serial"),
    ("USB Adapter", "/device-gateway/usb"),
    ("Simulator", "/device-gateway/simulator"),
    ("Device Queue", "/device-gateway/device-queue"),
    ("Retry Queue", "/device-gateway/retry-queue"),
    ("Device Audit", "/device-gateway/audit")
)


def hub_styles() -> str:
    return pilot_styles() + """
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; white-space:pre-wrap; font-size:13px; }
    .muted-note { color:#64748b; font-size:13px; margin-bottom:16px; }
    """


def render_hub_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in NAV)
    return f"""
    <html>
    <head><title>{title}</title><meta name="viewport" content="width=device-width, initial-scale=1" /><style>{hub_styles()}</style></head>
    <body><div class="wrap"><div class="nav">{nav}</div><div class="muted-note">Device Gateway · Phase 7.5</div>{body_html}</div></body>
    </html>
    """


def build_json_section(title: str, data: dict) -> str:
    return f"""
    {page_header(title, data.get("report", ""))}
    <div class="card"><pre>{html.escape(json.dumps(data, indent=2, default=str))}</pre></div>
    """


def build_dashboard_body() -> str:
    data = svc.dashboard_payload()
    summary = data.get("summary", {})
    cards = metric_cards([(k.replace("_", " ").title(), v) for k, v in list(summary.items())[:6]])
    features = "".join(f"<li>{html.escape(item)}</li>" for item in data.get("features", []))
    return f"""
    {page_header("Device Gateway", "Phase 7.5 enterprise hub.")}
    {cards}
    <div class="card"><h3>Features</h3><ul>{features}</ul></div>
    """


def build_gateway_registry_body() -> str:
    return build_json_section('Gateway Registry', svc.gateway_registry())

def build_astm_adapter_body() -> str:
    return build_json_section('ASTM Adapter', svc.astm_adapter())

def build_hl7_adapter_body() -> str:
    return build_json_section('HL7 Adapter', svc.hl7_adapter())

def build_tcp_adapter_body() -> str:
    return build_json_section('TCP Adapter', svc.tcp_adapter())

def build_serial_adapter_body() -> str:
    return build_json_section('Serial Adapter', svc.serial_adapter())

def build_usb_adapter_body() -> str:
    return build_json_section('USB Adapter', svc.usb_adapter())

def build_device_simulator_body() -> str:
    return build_json_section('Simulator', svc.device_simulator())

def build_device_queue_body() -> str:
    return build_json_section('Device Queue', svc.device_queue())

def build_retry_queue_body() -> str:
    return build_json_section('Retry Queue', svc.retry_queue())

def build_device_audit_body() -> str:
    return build_json_section('Device Audit', svc.device_audit())

