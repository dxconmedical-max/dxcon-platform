"""Data Warehouse web rendering helpers — Phase 7.7."""

from __future__ import annotations

import html
import json

from app.services import data_warehouse_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

NAV = (
    ("Overview", "/data-warehouse"),
    ("ETL Layer", "/data-warehouse/etl"),
    ("Fact Tables", "/data-warehouse/facts"),
    ("Dimension Tables", "/data-warehouse/dimensions"),
    ("Analytics API", "/data-warehouse/analytics"),
    ("BI Export", "/data-warehouse/bi-export"),
    ("PowerBI Export", "/data-warehouse/powerbi")
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
    <body><div class="wrap"><div class="nav">{nav}</div><div class="muted-note">Data Warehouse · Phase 7.7</div>{body_html}</div></body>
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
    {page_header("Data Warehouse", "Phase 7.7 enterprise hub.")}
    {cards}
    <div class="card"><h3>Features</h3><ul>{features}</ul></div>
    """


def build_etl_layer_body() -> str:
    return build_json_section('ETL Layer', svc.etl_layer())

def build_fact_tables_body() -> str:
    return build_json_section('Fact Tables', svc.fact_tables())

def build_dimension_tables_body() -> str:
    return build_json_section('Dimension Tables', svc.dimension_tables())

def build_analytics_api_body() -> str:
    return build_json_section('Analytics API', svc.analytics_api())

def build_bi_export_body() -> str:
    return build_json_section('BI Export', svc.bi_export())

def build_powerbi_export_body() -> str:
    return build_json_section('PowerBI Export', svc.powerbi_export())

