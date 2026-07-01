"""Staging monitoring stack validation."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
MONITORING = REPO / "deployment" / "monitoring"

PROMETHEUS_FILE = MONITORING / "prometheus.yml"
GRAFANA_DATASOURCES = MONITORING / "grafana" / "provisioning" / "datasources" / "datasources.yml"
GRAFANA_DASHBOARDS = MONITORING / "grafana" / "provisioning" / "dashboards" / "dashboards.yml"
GRAFANA_OVERVIEW = MONITORING / "grafana" / "dashboards" / "dxcon-overview.json"
LOKI_FILE = MONITORING / "loki" / "loki.yml"
ALERTMANAGER_FILE = MONITORING / "alertmanager" / "alertmanager.yml"


def verify_prometheus_config() -> dict:
    if not PROMETHEUS_FILE.exists():
        return {"ok": False, "error": "missing prometheus.yml"}
    text = PROMETHEUS_FILE.read_text(encoding="utf-8")
    checks = {
        "scrape_configs": "scrape_configs:" in text,
        "dxcon_api_job": 'job_name: dxcon-api' in text,
        "alertmanager_target": "alertmanager:9093" in text,
        "health_job": "dxcon-health" in text,
    }
    return {"ok": all(checks.values()), "checks": checks}


def verify_grafana_provisioning() -> dict:
    missing = [
        str(path.relative_to(REPO))
        for path in (GRAFANA_DATASOURCES, GRAFANA_DASHBOARDS, GRAFANA_OVERVIEW)
        if not path.exists()
    ]
    datasource_text = GRAFANA_DATASOURCES.read_text(encoding="utf-8") if GRAFANA_DATASOURCES.exists() else ""
    dashboard_text = GRAFANA_DASHBOARDS.read_text(encoding="utf-8") if GRAFANA_DASHBOARDS.exists() else ""
    checks = {
        "prometheus_datasource": "Prometheus" in datasource_text,
        "loki_datasource": "Loki" in datasource_text,
        "dashboard_provider": "providers:" in dashboard_text,
        "overview_dashboard": GRAFANA_OVERVIEW.exists(),
    }
    return {"ok": not missing and all(checks.values()), "missing": missing, "checks": checks}


def verify_loki_placeholder() -> dict:
    if not LOKI_FILE.exists():
        return {"ok": False, "error": "missing loki.yml"}
    text = LOKI_FILE.read_text(encoding="utf-8")
    return {
        "ok": "http_listen_port: 3100" in text and "placeholder" in text.lower(),
        "mode": "placeholder",
    }


def verify_alertmanager_placeholder() -> dict:
    if not ALERTMANAGER_FILE.exists():
        return {"ok": False, "error": "missing alertmanager.yml"}
    text = ALERTMANAGER_FILE.read_text(encoding="utf-8")
    return {
        "ok": "receivers:" in text and "placeholder" in text.lower(),
        "mode": "placeholder",
    }


def verify_route_inventory() -> dict:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from collections import defaultdict

    from app import create_app

    app = create_app()
    seen = defaultdict(list)
    for rule in app.url_map.iter_rules():
        methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
        key = (str(rule.rule), tuple(methods))
        seen[key].append(rule.endpoint)
    duplicates = {str(key): endpoints for key, endpoints in seen.items() if len(endpoints) > 1}
    return {"ok": not duplicates, "count": len(duplicates)}


def run_monitoring_verification() -> dict:
    from scripts.backup_restore_lib import run_backup_restore_verification

    checks = {
        "prometheus": verify_prometheus_config(),
        "grafana": verify_grafana_provisioning(),
        "loki": verify_loki_placeholder(),
        "alertmanager": verify_alertmanager_placeholder(),
        "backup_restore": run_backup_restore_verification(),
        "route_inventory": verify_route_inventory(),
    }
    passed = sum(1 for item in checks.values() if item.get("ok"))
    return {
        "ok": passed == len(checks),
        "passed": passed,
        "total": len(checks),
        "checks": checks,
    }
