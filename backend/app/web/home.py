from flask import Blueprint, current_app, redirect

from app.infrastructure.production_health import health_payload

home_web_bp = Blueprint("home_web", __name__)


def _status_color(status: str) -> str:
    normalized = (status or "").upper()
    if normalized in {"OK", "UP"}:
        return "#15803d"
    if normalized in {"DEGRADED", "WARNING"}:
        return "#b45309"
    return "#b91c1c"


@home_web_bp.route("/demo-landing")
def demo_landing():
    payload, _ = health_payload(current_app._get_current_object())
    status = payload.get("status", "UNKNOWN")
    app_env = payload.get("app_env", "unknown")
    database = payload.get("database", "UNKNOWN")
    redis = payload.get("redis", "UNKNOWN")
    timestamp = payload.get("timestamp", "")

    links = [
        ("Executive Dashboard", "/executive-v9"),
        ("CRM Pipeline", "/crm-pipeline"),
        ("Logistics Dashboard", "/logistics"),
        ("Reception Dashboard", "/reception"),
        ("Doctor Workbench", "/doctor-workbench"),
        ("Patient Portal Demo", "/patient-portal"),
        ("Demo Accounts", "/demo-accounts"),
        ("Workflow Demo", "/workflow-demo"),
        ("Pilot Checklist", "/pilot-checklist"),
        ("Collector Portal", "/collector"),
        ("Workflow Health", "/api/v1/workflow/health"),
        ("API Health", "/health"),
        ("Readiness", "/ready"),
        ("OpenAPI JSON", "/api/v1/openapi.json"),
        ("API Docs", "/api-docs"),
    ]
    link_items = "\n".join(
        f'<li><a href="{href}">{label}</a></li>' for label, href in links
    )

    return f"""
    <html>
    <head>
        <title>DxCon Platform</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
    </head>
    <body style="margin:0;font-family:Arial,Helvetica,sans-serif;background:#f8fafc;color:#0f172a;">
        <div style="max-width:960px;margin:0 auto;padding:32px 24px;">
            <header style="margin-bottom:24px;">
                <h1 style="margin:0 0 8px;font-size:32px;">DxCon Platform</h1>
                <p style="margin:0;color:#475569;">Pilot-ready operational demo landing page</p>
            </header>

            <section style="background:white;border-radius:12px;padding:24px;box-shadow:0 4px 16px rgba(15,23,42,.08);margin-bottom:24px;">
                <h2 style="margin-top:0;font-size:18px;">API Status</h2>
                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;">
                    <div style="background:#f1f5f9;border-radius:10px;padding:16px;">
                        <div style="font-size:12px;color:#64748b;">Status</div>
                        <div style="font-size:22px;font-weight:700;color:{_status_color(status)};">{status}</div>
                    </div>
                    <div style="background:#f1f5f9;border-radius:10px;padding:16px;">
                        <div style="font-size:12px;color:#64748b;">Environment</div>
                        <div style="font-size:22px;font-weight:700;">{app_env}</div>
                    </div>
                    <div style="background:#f1f5f9;border-radius:10px;padding:16px;">
                        <div style="font-size:12px;color:#64748b;">Database</div>
                        <div style="font-size:22px;font-weight:700;color:{_status_color(database)};">{database}</div>
                    </div>
                    <div style="background:#f1f5f9;border-radius:10px;padding:16px;">
                        <div style="font-size:12px;color:#64748b;">Redis</div>
                        <div style="font-size:22px;font-weight:700;color:{_status_color(redis)};">{redis}</div>
                    </div>
                </div>
                <p style="margin:16px 0 0;color:#64748b;font-size:13px;">Last probe: {timestamp}</p>
            </section>

            <section style="background:white;border-radius:12px;padding:24px;box-shadow:0 4px 16px rgba(15,23,42,.08);margin-bottom:24px;">
                <h2 style="margin-top:0;font-size:18px;">Pilot Pages</h2>
                <ul style="line-height:1.9;padding-left:20px;margin:0;">
                    <li><a href="/demo-accounts">Demo Accounts</a></li>
                    <li><a href="/workflow-demo">Workflow Demo</a></li>
                    <li><a href="/pilot-checklist">Pilot Checklist</a></li>
                </ul>
            </section>

            <section style="background:white;border-radius:12px;padding:24px;box-shadow:0 4px 16px rgba(15,23,42,.08);">
                <h2 style="margin-top:0;font-size:18px;">Demo Dashboards</h2>
                <ul style="line-height:1.9;padding-left:20px;margin:0;">
                    {link_items}
                </ul>
            </section>
        </div>
    </body>
    </html>
    """
