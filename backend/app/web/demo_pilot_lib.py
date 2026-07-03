"""Shared helpers for demo and workflow pilot dashboards."""

from __future__ import annotations

from typing import Any

from flask import current_app

from app.extensions.db import db
from app.infrastructure.production_health import health_payload
from app.infrastructure.schema_introspection import table_exists_name


DEMO_PATIENT_PREFIX = "DEMO-PAT-"
DEMO_ORDER_PREFIX = "DEMO-ORD-"
DEMO_TEST_PREFIX = "DEMO-TST-"

PILOT_NAV = (
    ("Home", "/"),
    ("Executive", "/executive-v9"),
    ("CRM Pipeline", "/crm-pipeline"),
    ("Logistics", "/logistics"),
    ("Reception", "/reception"),
    ("Doctor Workbench", "/doctor/dashboard"),
    ("Patient Portal", "/patient/demo"),
)


def pilot_styles() -> str:
    return """
    body { margin:0; font-family:Arial,Helvetica,sans-serif; background:#f8fafc; color:#0f172a; }
    .wrap { max-width:1100px; margin:0 auto; padding:28px 20px; }
    .nav { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:20px; }
    .nav a { color:#1d4ed8; text-decoration:none; background:white; padding:8px 12px; border-radius:8px; box-shadow:0 2px 8px rgba(15,23,42,.06); }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; }
    .card { background:white; border-radius:12px; padding:18px; box-shadow:0 4px 12px rgba(15,23,42,.08); margin-bottom:18px; }
    .metric h3 { margin:0 0 8px; font-size:13px; color:#64748b; font-weight:600; }
    .metric p { margin:0; font-size:28px; font-weight:700; }
    table { width:100%; border-collapse:collapse; background:white; }
    th, td { padding:10px 12px; border-bottom:1px solid #e2e8f0; text-align:left; font-size:14px; }
    th { background:#f1f5f9; }
    .notice { background:#fff7ed; border:1px solid #fed7aa; color:#9a3412; padding:14px 16px; border-radius:10px; margin-bottom:16px; }
    .ok { color:#15803d; font-weight:700; }
    .warn { color:#b45309; font-weight:700; }
    """


def status_class(value: str) -> str:
    normalized = (value or "").upper()
    if normalized in {"OK", "UP"}:
        return "ok"
    if normalized in {"DEGRADED", "WARNING"}:
        return "warn"
    return ""


def system_status() -> dict[str, Any]:
    payload, _ = health_payload(current_app._get_current_object())
    return {
        "status": payload.get("status", "UNKNOWN"),
        "app_env": payload.get("app_env", "unknown"),
        "database": payload.get("database", "UNKNOWN"),
        "redis": payload.get("redis", "UNKNOWN"),
        "timestamp": payload.get("timestamp", ""),
    }


def safe_query(model, *, filter_like: tuple[str, str] | None = None, limit: int | None = None):
    if model is None or not table_exists_name(model.__tablename__):
        return []
    try:
        query = model.query
        if filter_like:
            field_name, prefix = filter_like
            column = getattr(model, field_name)
            query = query.filter(column.like(f"{prefix}%"))
        if hasattr(model, "created_at"):
            query = query.order_by(model.created_at.desc())
        elif filter_like:
            field_name, _prefix = filter_like
            query = query.order_by(getattr(model, field_name))
        if limit:
            query = query.limit(limit)
        return query.all()
    except Exception:
        return []


def safe_count(model, *, prefix: str | None = None, field: str | None = None) -> int | None:
    if model is None or not table_exists_name(model.__tablename__):
        return None
    try:
        if prefix and field:
            column = getattr(model, field)
            return model.query.filter(column.like(f"{prefix}%")).count()
        return model.query.count()
    except Exception:
        return None


def seeded_summary() -> dict[str, Any]:
    from app.models.order import Order
    from app.models.patient import Patient
    from app.models.test_catalog import TestCatalog
    from app.models.user import User

    return {
        "users": safe_count(User, prefix="demo-", field="email") or 0,
        "patients": safe_count(Patient, prefix=DEMO_PATIENT_PREFIX, field="patient_code") or 0,
        "test_catalog": safe_count(TestCatalog, prefix=DEMO_TEST_PREFIX, field="code") or 0,
        "orders": safe_count(Order, prefix=DEMO_ORDER_PREFIX, field="order_code") or 0,
    }


def render_pilot_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in PILOT_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{pilot_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            {body_html}
        </div>
    </body>
    </html>
    """


def metric_cards(items: list[tuple[str, Any]]) -> str:
    cards = "".join(
        f'<div class="card metric"><h3>{label}</h3><p>{value}</p></div>' for label, value in items
    )
    return f'<div class="grid">{cards}</div>'


def system_status_cards(status: dict[str, Any]) -> str:
    return metric_cards(
        [
            ("Status", status["status"]),
            ("Environment", status["app_env"]),
            ("Database", status["database"]),
            ("Redis", status["redis"]),
        ]
    )
