"""Production Deployment web rendering helpers — Phase 5 Sprint 5.5."""

from __future__ import annotations

import html

from app.services import production_deployment_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

DEPLOYMENT_NAV = (
    ("Dashboard", "/production-deployment"),
    ("Docker", "/production-deployment/docker"),
    ("Nginx", "/production-deployment/nginx"),
    ("Probes", "/production-deployment/probes"),
    ("Rolling", "/production-deployment/rolling"),
    ("Migration", "/production-deployment/migration"),
    ("Release", "/production-deployment/release"),
    ("Rollback", "/production-deployment/rollback"),
)


def deployment_styles() -> str:
    return pilot_styles() + """
    .feature-list { font-size:13px; color:#334155; line-height:1.6; }
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; white-space:pre-wrap; }
    .checklist li { margin-bottom:10px; }
    """


def render_deployment_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in DEPLOYMENT_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{deployment_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted">Production deployment · Phase 5 Sprint 5.5</div>
            {body_html}
        </div>
    </body>
    </html>
    """


def _table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "<p class='muted'>No records.</p>"
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table><tr>{head}</tr>{body}</table>"


def _checks_list(checks: dict[str, bool] | list[dict]) -> str:
    if isinstance(checks, dict):
        return "".join(
            f"<li>{html.escape(key)}: {'PASS' if value else 'FAIL'}</li>"
            for key, value in checks.items()
        )
    return "".join(
        f"<li><strong>{html.escape(str(item.get('title', item.get('item', ''))))}</strong> "
        f"[{html.escape(str(item.get('status', '')))}]</li>"
        for item in checks
    )


def build_dashboard_body() -> str:
    data = svc.dashboard_payload()
    summary = data["summary"]
    cards = metric_cards(
        [
            ("Docker Checks", f"{summary['docker_checks_passed']}/{summary['docker_checks_total']}"),
            ("Nginx Checks", f"{summary['nginx_checks_passed']}/{summary['nginx_checks_total']}"),
            ("Migration Checks", f"{summary['migration_checks_passed']}/{summary['migration_checks_total']}"),
            ("Deploy Score", summary["deployment_score"]),
            ("Runtime", summary["runtime_profile"]),
        ]
    )
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    return f"""
    {page_header("Production Deployment", "Docker, nginx, probes, rolling deploy, migration, release, and rollback.")}
    <div class="card"><strong>Status:</strong> {html.escape(data['status'])}</div>
    {cards}
    <div class="card"><h3>Features</h3><ul class="feature-list">{features}</ul></div>
    """


def build_docker_body() -> str:
    data = svc.docker_production_profile()
    rows = [[html.escape(k), "PASS" if v else "FAIL"] for k, v in data.get("checks", {}).items()]
    return f"""
    {page_header("Docker Production Profile", data.get("compose_file", ""))}
    <div class="card"><p>Checks: {data.get('checks_passed', 0)}/{data.get('checks_total', 0)}</p></div>
    <div class="card"><h3>Validation</h3>{_table(["Check", "Status"], rows)}</div>
    """


def build_nginx_body() -> str:
    data = svc.nginx_production()
    rows = [[html.escape(k), "PASS" if v else "FAIL"] for k, v in data.get("checks", {}).items()]
    return f"""
    {page_header("Nginx Production", "Reverse proxy, security headers, and health routes.")}
    <div class="card"><p>Checks: {data.get('checks_passed', 0)}/{data.get('checks_total', 0)}</p></div>
    <div class="card"><h3>Validation</h3>{_table(["Check", "Status"], rows)}</div>
    """


def build_probes_body() -> str:
    data = svc.health_probes()
    rows = [
        [html.escape(data["live_probe"]["path"]), str(data["live_probe"]["status_code"])],
        [html.escape(data["ready_probe"]["path"]), str(data["ready_probe"]["status_code"])],
        [html.escape(data["health_probe"]["path"]), str(data["health_probe"]["status_code"])],
    ]
    flags = [
        ("Docker HEALTHCHECK", data.get("docker_healthcheck")),
        ("Compose healthcheck", data.get("compose_healthcheck")),
        ("K8s readiness", data.get("kubernetes_readiness")),
        ("K8s liveness", data.get("kubernetes_liveness")),
        ("Nginx /live", data.get("nginx_live_route")),
    ]
    flag_rows = [[html.escape(name), "Yes" if ok else "No"] for name, ok in flags]
    return f"""
    {page_header("Health Probes", "Live, ready, and health endpoints for zero-downtime cutover.")}
    <div class="card"><h3>Probe Responses</h3>{_table(["Path", "Status Code"], rows)}</div>
    <div class="card"><h3>Probe Configuration</h3>{_table(["Layer", "Configured"], flag_rows)}</div>
    """


def build_rolling_body() -> str:
    data = svc.rolling_deployment()
    steps = "".join(f"<li>{html.escape(step)}</li>" for step in data.get("steps", []))
    return f"""
    {page_header("Rolling Deployment", "Health-gated rollout across replicas.")}
    <div class="card"><p>Strategy: {html.escape(str(data.get('strategy', {})))}</p>
    <p>Replicas: {data.get('replicas', 0)}</p></div>
    <div class="card"><h3>Steps</h3><ol class="checklist">{steps}</ol></div>
    <div class="card"><h3>Legacy API</h3><pre>{html.escape(data.get('legacy_api', ''))}</pre></div>
    """


def build_migration_body() -> str:
    data = svc.zero_downtime_migration()
    checks = _checks_list(data.get("checks", []))
    return f"""
    {page_header("Zero-downtime Migration", "Migration readiness gated by /ready probe.")}
    <div class="card"><p>Checks: {data.get('checks_passed', 0)}/{data.get('checks_total', 0)}</p></div>
    <div class="card"><h3>Checklist</h3><ul class="checklist">{checks}</ul></div>
    """


def build_release_body() -> str:
    data = svc.release_checklist()
    items = "".join(
        f"<li>{'[x]' if item.get('checked') else '[ ]'} {html.escape(item.get('item', ''))}</li>"
        for item in data.get("items", [])
    )
    scripts = "".join(f"<li>{html.escape(item)}</li>" for item in data.get("verify_scripts", []))
    return f"""
    {page_header("Release Checklist", "Pre-cutover verification before production promotion.")}
    <div class="card"><h3>Checklist</h3><ul class="checklist">{items}</ul></div>
    <div class="card"><h3>Verify Scripts</h3><ul class="checklist">{scripts}</ul></div>
    <div class="card"><h3>Legacy API</h3><pre>{html.escape(data.get('legacy_api', ''))}</pre></div>
    """


def build_rollback_body() -> str:
    data = svc.rollback_checklist()
    items = "".join(
        f"<li>{html.escape(str(item.get('item', '')))}</li>" for item in data.get("items", [])
    )
    steps = "".join(f"<li>{html.escape(step)}</li>" for step in data.get("pipeline_steps", []))
    return f"""
    {page_header("Rollback Checklist", "Non-destructive rollback plan and verification steps.")}
    <div class="card"><h3>Checklist</h3><ol class="checklist">{items}</ol></div>
    <div class="card"><h3>Pipeline Steps</h3><ol class="checklist">{steps}</ol></div>
    <div class="card"><h3>Legacy API</h3><pre>{html.escape(data.get('legacy_api', ''))}</pre></div>
    """
