"""Shared helpers for demo and workflow pilot dashboards."""

from __future__ import annotations

from typing import Any, Callable

from flask import current_app

from app.extensions.db import db
from app.infrastructure.production_health import health_payload
from app.infrastructure.schema_introspection import table_exists_name

DEMO_DOMAIN = "demo.dxcon.test"
DEMO_PASSWORD = "DemoPass123!"
DEMO_PATIENT_PREFIX = "DEMO-PAT-"
DEMO_ORDER_PREFIX = "DEMO-ORD-"
DEMO_TEST_PREFIX = "DEMO-TST-"

PILOT_NAV = (
    ("Home", "/"),
    ("Executive", "/executive-v9"),
    ("CRM", "/crm-pipeline"),
    ("Logistics", "/logistics"),
    ("Reception", "/reception"),
    ("Doctor", "/doctor-workbench"),
    ("Patient", "/patient-portal"),
    ("Demo Accounts", "/demo-accounts"),
    ("Workflow", "/workflow-demo"),
    ("Checklist", "/pilot-checklist"),
)


def pilot_styles() -> str:
    return """
    body { margin:0; font-family:Inter,Arial,Helvetica,sans-serif; background:#f1f5f9; color:#0f172a; }
    .wrap { max-width:1180px; margin:0 auto; padding:28px 20px 48px; }
    .nav { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:22px; }
    .nav a { color:#1e3a8a; text-decoration:none; background:white; padding:8px 12px; border-radius:999px; border:1px solid #dbeafe; font-size:13px; }
    .nav a:hover { background:#eff6ff; }
    .hero { background:linear-gradient(135deg,#1e3a8a,#0f766e); color:white; border-radius:16px; padding:28px; margin-bottom:22px; box-shadow:0 10px 30px rgba(15,23,42,.12); }
    .hero h1 { margin:0 0 8px; font-size:30px; }
    .hero p { margin:0; opacity:.92; line-height:1.5; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; }
    .card { background:white; border-radius:14px; padding:20px; box-shadow:0 4px 16px rgba(15,23,42,.06); margin-bottom:18px; border:1px solid #e2e8f0; }
    .card h2 { margin:0 0 14px; font-size:18px; }
    .metric h3 { margin:0 0 8px; font-size:12px; color:#64748b; font-weight:700; text-transform:uppercase; letter-spacing:.04em; }
    .metric p { margin:0; font-size:28px; font-weight:700; color:#0f172a; }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:11px 12px; border-bottom:1px solid #e2e8f0; text-align:left; font-size:14px; }
    th { background:#f8fafc; color:#475569; font-size:12px; text-transform:uppercase; letter-spacing:.03em; }
    tr:hover td { background:#fafafa; }
    .notice { background:#fff7ed; border:1px solid #fed7aa; color:#9a3412; padding:14px 16px; border-radius:12px; margin-bottom:16px; }
    .ok { color:#15803d; font-weight:700; }
    .warn { color:#b45309; font-weight:700; }
    .bad { color:#b91c1c; font-weight:700; }
    .badge { display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:700; background:#eff6ff; color:#1d4ed8; }
    .steps { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; }
    .step { background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:14px; text-align:center; }
    .step strong { display:block; margin-bottom:6px; color:#1e3a8a; }
    .checklist-row { display:flex; justify-content:space-between; gap:12px; padding:12px 0; border-bottom:1px solid #e2e8f0; }
    .muted { color:#64748b; }
    .links a { margin-right:14px; }
    """


def page_header(title: str, subtitle: str) -> str:
    return f"""
    <div class="hero">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """


def status_class(value: str) -> str:
    normalized = (value or "").upper()
    if normalized in {"OK", "UP", "PASS", "READY"}:
        return "ok"
    if normalized in {"DEGRADED", "WARNING", "PARTIAL"}:
        return "warn"
    if normalized in {"FAIL", "ERROR", "DOWN"}:
        return "bad"
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


def safe_all(model) -> list[Any]:
    return safe_query(model)


def safe_count(model, *, prefix: str | None = None, field: str | None = None) -> int:
    if model is None or not table_exists_name(model.__tablename__):
        return 0
    try:
        if prefix and field:
            column = getattr(model, field)
            return model.query.filter(column.like(f"{prefix}%")).count()
        return model.query.count()
    except Exception:
        return 0


def seeded_summary() -> dict[str, int]:
    from app.models.order import Order
    from app.models.patient import Patient
    from app.models.test_catalog import TestCatalog
    from app.models.user import User

    return {
        "users": safe_count(User, prefix="demo-", field="email"),
        "patients": safe_count(Patient, prefix=DEMO_PATIENT_PREFIX, field="patient_code"),
        "test_catalog": safe_count(TestCatalog, prefix=DEMO_TEST_PREFIX, field="code"),
        "orders": safe_count(Order, prefix=DEMO_ORDER_PREFIX, field="order_code"),
    }


def demo_accounts_by_role() -> dict[str, list[dict[str, str]]]:
    from app.models.driver import Driver
    from app.models.laboratory import Laboratory
    from app.models.patient import Patient
    from app.models.user import User

    accounts: dict[str, list[dict[str, str]]] = {
        "admin": [],
        "doctor": [],
        "lab": [],
        "reception": [],
        "collector": [],
        "patient": [],
    }
    try:
        for user in User.query.filter(User.email.like("demo-%")).order_by(User.email).all():
            entry = {"email": user.email, "role": user.role, "password": DEMO_PASSWORD}
            role = (user.role or "").upper()
            if role in {"SUPER_ADMIN", "ADMIN", "ACCOUNTING"}:
                accounts["admin"].append(entry)
            elif role == "DOCTOR":
                accounts["doctor"].append(entry)
            elif role in {"LAB", "LABORATORY"}:
                accounts["lab"].append(entry)
            elif role in {"COLLECTOR", "DRIVER"}:
                accounts["collector"].append(entry)
    except Exception:
        pass

    try:
        for lab in safe_query(Laboratory, filter_like=("code", "DEMO-LAB-"), limit=5):
            accounts["lab"].append(
                {
                    "email": lab.email or f"{lab.code.lower()}@{DEMO_DOMAIN}",
                    "role": "LAB",
                    "password": DEMO_PASSWORD,
                }
            )
    except Exception:
        pass

    try:
        for driver in safe_query(Driver, filter_like=("driver_code", "DEMO-COL-"), limit=5):
            accounts["collector"].append(
                {
                    "email": driver.email or f"{driver.driver_code.lower()}@{DEMO_DOMAIN}",
                    "role": "COLLECTOR",
                    "password": DEMO_PASSWORD,
                }
            )
    except Exception:
        pass

    accounts["reception"].append(
        {
            "email": "Use Admin demo account for reception desk pilot",
            "role": "RECEPTION",
            "password": DEMO_PASSWORD,
        }
    )

    try:
        for patient in safe_query(Patient, filter_like=("patient_code", DEMO_PATIENT_PREFIX), limit=5):
            accounts["patient"].append(
                {
                    "email": patient.email or f"{patient.patient_code.lower()}@{DEMO_DOMAIN}",
                    "role": "PATIENT",
                    "password": "Portal via /patient-portal (no shared login required for demo list)",
                }
            )
    except Exception:
        pass

    return accounts


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


def render_safe_page(title: str, subtitle: str, builder: Callable[[], str]) -> str:
    try:
        body = builder()
        return render_pilot_page(title, body)
    except Exception as exc:
        fallback = f"""
        {page_header(title, subtitle)}
        <div class="notice">
            This dashboard is in pilot-safe mode. Live data could not be loaded ({exc}).
            Use seeded demo pages and workflow checklist while data is being aligned.
        </div>
        <div class="card links">
            <a href="/">Home</a>
            <a href="/demo-accounts">Demo Accounts</a>
            <a href="/pilot-checklist">Pilot Checklist</a>
        </div>
        """
        return render_pilot_page(title, fallback)


def metric_cards(items: list[tuple[str, Any]]) -> str:
    cards = "".join(
        f'<div class="card metric"><h3>{label}</h3><p>{value}</p></div>' for label, value in items
    )
    return f'<div class="grid">{cards}</div>'


def system_status_cards(status: dict[str, Any]) -> str:
    return metric_cards(
        [
            ("Status", f'<span class="{status_class(status["status"])}">{status["status"]}</span>'),
            ("Environment", status["app_env"]),
            ("Database", f'<span class="{status_class(status["database"])}">{status["database"]}</span>'),
            ("Redis", f'<span class="{status_class(status["redis"])}">{status["redis"]}</span>'),
        ]
    )


def account_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "<p class='muted'>No demo accounts found for this role.</p>"
    body = "".join(
        f"<tr><td>{row['email']}</td><td><span class='badge'>{row['role']}</span></td><td>{row['password']}</td></tr>"
        for row in rows
    )
    return f"<table><tr><th>Account</th><th>Role</th><th>Access</th></tr>{body}</table>"
