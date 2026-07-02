"""Enterprise Hardening Pack 5 - Operations Excellence verification."""

from __future__ import annotations

from pathlib import Path

from scripts.enterprise_master_lib import (
    REPO,
    ROOT,
    create_test_app,
    run_compileall,
    run_release_isolation,
    run_unit_tests,
    score_from_checks,
    utc_now,
    write_report,
)

RELEASE_ID = "enterprise-hardening-pack-5"


def _exists(*parts) -> bool:
    return (REPO.joinpath(*parts)).exists()


def run_operations_review() -> dict:
    checks = {
        "health_endpoints": {
            "ok": _exists("backend", "app", "api", "system", "routes.py"),
            "paths": ["/api/v1/system/health", "/api/v1/system/ready", "/api/v1/system/live"],
        },
        "observability_platform": {
            "ok": _exists("backend", "app", "observability"),
            "metrics": _exists("backend", "app", "api", "observability"),
        },
        "operations_platform": {
            "ok": _exists("backend", "app", "api", "operations"),
            "maintenance": _exists("backend", "app", "operations", "maintenance_service.py"),
        },
        "deployment_readiness": {
            "ok": _exists("backend", "app", "infrastructure", "production_readiness.py"),
        },
    }
    report = {
        "generated_at": utc_now(),
        "release": RELEASE_ID,
        "checks": checks,
        "score": score_from_checks(checks),
        "ok": all(item.get("ok") for item in checks.values()),
    }
    write_report("operations_review.json", report)
    return report


def run_backup_review() -> dict:
    checks = {
        "backup_restore_lib": {"ok": _exists("backend", "scripts", "backup_restore_lib.py")},
        "backup_scripts": {
            "ok": _exists("deployment", "scripts", "backup_postgres.sh"),
            "restore_dry_run": _exists("deployment", "scripts", "restore_postgres_dry_run.sh"),
        },
        "operations_backup_api": {
            "ok": _exists("backend", "app", "api", "operations", "routes.py"),
        },
    }
    report = {
        "generated_at": utc_now(),
        "release": RELEASE_ID,
        "checks": checks,
        "ok": all(item.get("ok") for item in checks.values()),
    }
    write_report("backup_review.json", report)
    return report


def run_monitoring_review() -> dict:
    checks = {
        "prometheus_config": {"ok": _exists("deployment", "monitoring", "prometheus.yml")},
        "grafana_provisioning": {
            "ok": _exists("deployment", "monitoring", "grafana", "provisioning", "datasources", "datasources.yml"),
            "dashboards": _exists("deployment", "monitoring", "grafana", "provisioning", "dashboards", "dashboards.yml"),
        },
        "alert_rules": {"ok": _exists("deployment", "monitoring", "alerts", "dxcon-alerts.yml")},
        "alertmanager": {"ok": _exists("deployment", "monitoring", "alertmanager", "alertmanager.yml")},
        "monitoring_verify": {"ok": _exists("backend", "scripts", "verify_monitoring_stack.py")},
    }
    report = {
        "generated_at": utc_now(),
        "release": RELEASE_ID,
        "checks": checks,
        "score": score_from_checks(checks),
        "ok": all(item.get("ok") for item in checks.values()),
    }
    write_report("monitoring_review.json", report)
    return report


def check_health_probes(app) -> dict:
    from app.extensions.db import db

    with app.app_context():
        db.create_all()
        client = app.test_client()
        probes = {
            "health": client.get("/api/v1/system/health"),
            "ready": client.get("/api/v1/system/ready"),
            "live": client.get("/api/v1/system/live"),
        }
    return {
        "ok": (
            probes["health"].status_code == 200
            and probes["live"].status_code == 200
            and probes["ready"].status_code in {200, 503}
        ),
        "status_codes": {name: resp.status_code for name, resp in probes.items()},
    }


def run_operations_excellence_verification() -> dict:
    compile_result = run_compileall()
    app, _db = create_test_app()
    ops = run_operations_review()
    backup = run_backup_review()
    monitoring = run_monitoring_review()
    with app.app_context():
        health = check_health_probes(app)
    ops["checks"]["runtime_health_probes"] = health
    ops["ok"] = all(item.get("ok") for item in ops["checks"].values())
    write_report("operations_review.json", ops)
    tests = run_unit_tests()
    sections = {
        "compile": compile_result,
        "operations_review": ops,
        "backup_review": backup,
        "monitoring_review": monitoring,
        "unit_tests": tests,
    }
    ok = all(section.get("ok") for section in sections.values())
    return {"ok": ok, "sections": sections, "score": monitoring.get("score", 0)}
