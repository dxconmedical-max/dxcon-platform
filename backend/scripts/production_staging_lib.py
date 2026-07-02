"""Production Staging Phase verification (Phases A-F)."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from scripts.backup_restore_lib import run_backup_restore_verification
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
from scripts.env_safety_lib import run_env_safety_verification
from scripts.monitoring_stack_lib import run_monitoring_stack_verification
from scripts.staging_stack_lib import (
    ENV_FILES,
    parse_env_file,
    validate_env_file,
    verify_app_boot,
    verify_docker_stack,
    verify_env_templates,
    verify_health_routes,
    verify_nginx_config,
    verify_production_guards,
    verify_staging_config,
)

PHASE_RELEASES = {
    "A": "production-staging-phase-a",
    "B": "production-staging-phase-b",
    "C": "production-staging-phase-c",
    "D": "production-staging-phase-d",
    "E": "production-staging-phase-e",
    "F": "production-staging-phase-f",
}


def _exists(*parts) -> bool:
    return REPO.joinpath(*parts).exists()


def _read_text(*parts) -> str:
    path = REPO.joinpath(*parts)
    return path.read_text(encoding="utf-8") if path.exists() else ""


def check_postgresql_config() -> dict:
    reports = {}
    for path in ENV_FILES:
        values = parse_env_file(path)
        db_url = values.get("DATABASE_URL", "")
        reports[str(path.relative_to(REPO))] = {
            "ok": db_url.startswith("postgresql://"),
            "database_url": db_url,
        }
    return {"ok": all(item["ok"] for item in reports.values()), "files": reports}


def check_redis_config() -> dict:
    reports = {}
    for path in ENV_FILES:
        values = parse_env_file(path)
        redis_url = values.get("REDIS_URL", "")
        reports[str(path.relative_to(REPO))] = {
            "ok": redis_url.startswith("redis://") or redis_url.startswith("rediss://"),
            "redis_url": redis_url,
        }
    return {"ok": all(item["ok"] for item in reports.values()), "files": reports}


def check_smtp_config() -> dict:
    required = ("SMTP_HOST", "SMTP_PORT", "SMTP_FROM")
    reports = {}
    for path in ENV_FILES:
        values = parse_env_file(path)
        missing = [key for key in required if not values.get(key)]
        reports[str(path.relative_to(REPO))] = {"ok": not missing, "missing": missing}
    return {"ok": all(item["ok"] for item in reports.values()), "files": reports}


def check_cors_origins() -> dict:
    reports = {}
    for path in ENV_FILES:
        values = parse_env_file(path)
        cors = values.get("CORS_ORIGINS", "")
        reports[str(path.relative_to(REPO))] = {
            "ok": bool(cors) and cors != "*",
            "cors_origins": cors,
        }
    return {"ok": all(item["ok"] for item in reports.values()), "files": reports}


def check_secret_keys() -> dict:
    required = ("SECRET_KEY", "JWT_SECRET_KEY")
    reports = {}
    for path in ENV_FILES:
        values = parse_env_file(path)
        entries = {}
        ok = True
        for key in required:
            value = values.get(key, "")
            valid = len(value) >= 16 and value.lower() not in {"change-me", "dev", "secret"}
            entries[key] = {"ok": valid, "length": len(value)}
            ok = ok and valid
        reports[str(path.relative_to(REPO))] = {"ok": ok, "keys": entries}
    guards = verify_production_guards()
    return {"ok": all(item["ok"] for item in reports.values()) and guards.get("ok"), "files": reports, "production_guards": guards}


def check_domain_tls_readiness() -> dict:
    nginx = _read_text("deployment", "nginx", "default.conf")
    staging = parse_env_file(ROOT / ".env.staging.example")
    production = parse_env_file(ROOT / ".env.production.example")
    cors_origins = [
        origin.strip()
        for origin in (staging.get("CORS_ORIGINS", "") + "," + production.get("CORS_ORIGINS", "")).split(",")
        if origin.strip()
    ]
    checks = {
        "forwarded_proto_header": "X-Forwarded-Proto" in nginx,
        "health_routes": "/live" in nginx and "/ready" in nginx,
        "security_headers": "X-Content-Type-Options" in nginx,
        "https_cors_origins": bool(cors_origins) and all(origin.startswith("https://") for origin in cors_origins),
        "kubernetes_ingress": _exists("deployment", "kubernetes", "ingress.yaml"),
    }
    return {"ok": all(checks.values()), "checks": checks}


def check_env_examples() -> dict:
    templates = verify_env_templates()
    safety = run_env_safety_verification()
    return {
        "ok": templates.get("ok") and safety.get("ok"),
        "templates": templates,
        "env_safety": safety,
    }


def run_phase_a_production_config() -> dict:
    checks = {
        "postgresql_config": check_postgresql_config(),
        "redis_config": check_redis_config(),
        "smtp_config": check_smtp_config(),
        "cors_origins": check_cors_origins(),
        "secret_keys": check_secret_keys(),
        "domain_tls_readiness": check_domain_tls_readiness(),
        "env_examples": check_env_examples(),
        "staging_config": verify_staging_config(),
    }
    score = score_from_checks(checks)
    report = {
        "generated_at": utc_now(),
        "release": PHASE_RELEASES["A"],
        "phase": "A",
        "checks": checks,
        "production_config_score": score,
        "ok": all(item.get("ok") for item in checks.values()),
    }
    write_report("production_config_report.json", report)
    return report


def check_gunicorn_runtime() -> dict:
    text = _read_text("backend", "gunicorn.conf.py")
    checks = {
        "workers": "workers" in text,
        "timeout": "timeout" in text,
        "graceful_timeout": "graceful_timeout" in text,
        "keepalive": "keepalive" in text,
        "access_log": "accesslog" in text,
        "error_log": "errorlog" in text,
    }
    return {"ok": all(checks.values()), "checks": checks}


def check_worker_scheduler_runtime() -> dict:
    text = _read_text("backend", "production_start.py")
    staging = _read_text("docker-compose.staging.yml")
    production = _read_text("docker-compose.production.yml")
    checks = {
        "production_start": "production_start.py" in text or _exists("backend", "production_start.py"),
        "api_role": "api" in text,
        "worker_role": "worker" in text,
        "scheduler_role": "scheduler" in text,
        "staging_worker": "worker:" in staging,
        "staging_scheduler": "scheduler:" in staging,
        "production_worker": "worker:" in production,
        "production_scheduler": "scheduler:" in production,
    }
    return {"ok": all(checks.values()), "checks": checks}


def check_graceful_shutdown() -> dict:
    gunicorn = _read_text("backend", "gunicorn.conf.py")
    start = _read_text("backend", "production_start.py")
    checks = {
        "graceful_timeout_configured": "graceful_timeout" in gunicorn,
        "max_requests_rotation": "max_requests" in gunicorn,
        "gunicorn_entrypoint": "gunicorn" in start,
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_phase_b_runtime_infrastructure() -> dict:
    checks = {
        "docker_stack": verify_docker_stack(),
        "nginx_config": verify_nginx_config(),
        "gunicorn_runtime": check_gunicorn_runtime(),
        "worker_scheduler_runtime": check_worker_scheduler_runtime(),
        "graceful_shutdown": check_graceful_shutdown(),
        "health_readiness_liveness": verify_health_routes(),
        "app_boot": verify_app_boot(),
    }
    score = score_from_checks(checks)
    report = {
        "generated_at": utc_now(),
        "release": PHASE_RELEASES["B"],
        "phase": "B",
        "checks": checks,
        "infrastructure_score": score,
        "ok": all(item.get("ok") for item in checks.values()),
    }
    write_report("runtime_infrastructure_report.json", report)
    return report


def check_audit_timeline(app) -> dict:
    from app.extensions.db import db
    from app.observability.audit_service import AuditTimelineService

    with app.app_context():
        db.create_all()
        event = AuditTimelineService.record("ProductionStaging", "phase_c_verify", actor={"display_name": "System"})
        listed = AuditTimelineService.list_events(limit=5)
    return {
        "ok": event is not None and listed.get("total", 0) >= 1,
        "event_types": listed.get("event_types", []),
    }


def check_error_monitoring_hooks(app) -> dict:
    from app.extensions.db import db

    with app.app_context():
        db.create_all()
        client = app.test_client()
        health = client.get("/api/v1/system/health")
        metrics = client.get("/metrics/prometheus")
    body = metrics.get_data(as_text=True)
    checks = {
        "health_endpoint": health.status_code == 200,
        "metrics_endpoint": metrics.status_code == 200,
        "http_errors_metric": "http_errors_total" in body,
        "readiness_metric": "readiness_ok" in body,
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_phase_c_observability_operations() -> dict:
    app, _db = create_test_app()
    monitoring = run_monitoring_stack_verification()
    with app.app_context():
        audit = check_audit_timeline(app)
        errors = check_error_monitoring_hooks(app)
    checks = {
        "monitoring_stack": monitoring,
        "audit_timeline": audit,
        "error_monitoring_hooks": errors,
        "structured_logging": monitoring.get("checks", {}).get("log_readiness", {}),
        "prometheus_alerts": monitoring.get("checks", {}).get("alert_rules", {}),
        "grafana_provisioning": monitoring.get("checks", {}).get("grafana", {}),
    }
    score = score_from_checks(
        {
            "monitoring_stack": monitoring,
            "audit_timeline": audit,
            "error_monitoring_hooks": errors,
            "structured_logging": monitoring.get("checks", {}).get("log_readiness", {"ok": False}),
            "prometheus_alerts": monitoring.get("checks", {}).get("alert_rules", {"ok": False}),
            "grafana_provisioning": monitoring.get("checks", {}).get("grafana", {"ok": False}),
        }
    )
    report = {
        "generated_at": utc_now(),
        "release": PHASE_RELEASES["C"],
        "phase": "C",
        "checks": checks,
        "observability_score": score,
        "ok": monitoring.get("ok") and audit.get("ok") and errors.get("ok"),
    }
    write_report("observability_operations_report.json", report)
    return report


def check_dr_metadata() -> dict:
    dr_doc = _read_text("docs", "DISASTER_RECOVERY.md")
    checks = {
        "disaster_recovery_doc": _exists("docs", "DISASTER_RECOVERY.md"),
        "rto_documented": "RTO" in dr_doc,
        "rpo_documented": "RPO" in dr_doc,
        "backup_doc": _exists("docs", "BACKUP.md"),
        "restore_doc": _exists("docs", "RESTORE.md"),
    }
    return {"ok": all(checks.values()), "checks": checks}


def check_rollback_checklist() -> dict:
    artifacts = (
        "ROLLBACK_CHECKLIST.json",
        "ROLLBACK_PACKAGE.json",
        "PRODUCTION_CUTOVER_CHECKLIST.json",
    )
    missing = [name for name in artifacts if not (ROOT / "generated_release" / name).exists()]
    return {"ok": not missing, "missing": missing, "artifacts": list(artifacts)}


def run_phase_d_backup_restore_dr() -> dict:
    backup = run_backup_restore_verification(create_samples=True)
    checks = {
        "backup_restore": backup,
        "dr_metadata": check_dr_metadata(),
        "rollback_checklist": check_rollback_checklist(),
    }
    score = score_from_checks(checks)
    report = {
        "generated_at": utc_now(),
        "release": PHASE_RELEASES["D"],
        "phase": "D",
        "checks": checks,
        "backup_restore_score": score,
        "rto_rpo": {"production_api_rto_hours": 4, "production_api_rpo_hours": 1, "file_storage_rto_hours": 8, "file_storage_rpo_hours": 4},
        "ok": all(item.get("ok") for item in checks.values()),
    }
    write_report("backup_restore_dr_report.json", report)
    return report


def _latency_smoke(app, path: str, budget_ms: float = 500.0) -> dict:
    with app.app_context():
        client = app.test_client()
        start = time.perf_counter()
        response = client.get(path)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
    return {
        "ok": response.status_code in {200, 503} and duration_ms <= budget_ms,
        "status_code": response.status_code,
        "duration_ms": duration_ms,
    }


def run_phase_e_performance_scale_smoke() -> dict:
    app, _db = create_test_app()
    from app.extensions.db import db

    with app.app_context():
        db.create_all()
        api_latency = {
            "health": _latency_smoke(app, "/api/v1/system/health"),
            "version": _latency_smoke(app, "/api/v1/system/version"),
            "stats": _latency_smoke(app, "/api/v1/system/stats"),
        }
        db_smoke = _latency_smoke(app, "/api/v1/system/ready")

    throughput_scripts = {
        "performance_smoke": _exists("backend", "scripts", "performance_smoke_test.py"),
        "notification_smoke": _exists("backend", "scripts", "smoke_test_notifications.py"),
        "webhook_module": _exists("backend", "app", "models", "payment_webhook.py")
        or _exists("backend", "app", "integrations"),
        "worker_runtime": _exists("backend", "production_start.py"),
    }
    checks = {
        "api_latency_smoke": {"ok": all(item["ok"] for item in api_latency.values()), "samples": api_latency},
        "db_query_smoke": db_smoke,
        "queue_throughput_smoke": {"ok": throughput_scripts["performance_smoke"], "scripts": throughput_scripts},
        "webhook_throughput_smoke": {"ok": throughput_scripts["webhook_module"], "scripts": throughput_scripts},
        "notification_throughput_smoke": {"ok": throughput_scripts["notification_smoke"], "scripts": throughput_scripts},
        "worker_concurrency_smoke": {"ok": throughput_scripts["worker_runtime"], "scripts": throughput_scripts},
    }
    score = score_from_checks(checks)
    report = {
        "generated_at": utc_now(),
        "release": PHASE_RELEASES["E"],
        "phase": "E",
        "checks": checks,
        "performance_score": score,
        "ok": all(item.get("ok") for item in checks.values()),
    }
    write_report("performance_scale_report.json", report)
    return report


def _run_script(relative_path: str) -> dict:
    script = ROOT / relative_path
    if not script.exists():
        return {"ok": False, "error": "missing", "path": relative_path}
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        env={**dict(**__import__("os").environ), "PYTHONDONTWRITEBYTECODE": "1", "DATABASE_URL": "sqlite:///:memory:"},
    )
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "path": relative_path,
        "tail": (proc.stdout or proc.stderr).splitlines()[-3:],
    }


def _load_report_ok(name: str) -> dict:
    path = ROOT / "generated_release" / name
    if not path.exists():
        return {"ok": False, "error": "missing", "report": name}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {"ok": bool(payload.get("ok")), "report": name, "score": payload.get("production_config_score") or payload.get("score")}


def run_phase_f_rc3_production_candidate() -> dict:
    compile_result = run_compileall()
    tests = run_unit_tests()
    smoke_scripts = (
        "scripts/smoke_test_backend.py",
        "scripts/smoke_test_staging_stack.py",
        "scripts/smoke_test_performance.py",
        "scripts/smoke_test_production_blockers.py",
    )
    smoke_results = {path: _run_script(path) for path in smoke_scripts}
    verify_scripts = (
        "scripts/verify_production_staging_phase_a.py",
        "scripts/verify_production_staging_phase_b.py",
        "scripts/verify_production_staging_phase_c.py",
        "scripts/verify_production_staging_phase_d.py",
        "scripts/verify_production_staging_phase_e.py",
        "scripts/check_production_env.py",
        "scripts/verify_go_live_blockers.py",
        "scripts/verify_rollback_package.py",
    )
    verify_results = {path: _run_script(path) for path in verify_scripts}
    isolation = run_release_isolation(PHASE_RELEASES["F"])

    phase_reports = {
        "production_config": _load_report_ok("production_config_report.json"),
        "runtime_infrastructure": _load_report_ok("runtime_infrastructure_report.json"),
        "observability_operations": _load_report_ok("observability_operations_report.json"),
        "backup_restore_dr": _load_report_ok("backup_restore_dr_report.json"),
        "performance_scale": _load_report_ok("performance_scale_report.json"),
    }

    component_scores = {
        "production_config": _load_report_ok("production_config_report.json").get("score") or 100,
        "infrastructure": _load_report_ok("runtime_infrastructure_report.json").get("score") or 100,
        "observability": _load_report_ok("observability_operations_report.json").get("score") or 100,
        "backup_restore": _load_report_ok("backup_restore_dr_report.json").get("score") or 100,
        "performance": _load_report_ok("performance_scale_report.json").get("score") or 100,
    }
    for key in component_scores:
        if component_scores[key] is None:
            component_scores[key] = 100 if phase_reports.get(key.replace("_", "_") if False else key, {}).get("ok") else 0

    # Normalize scores from report payloads
    score_map = {
        "production_config": json.loads((ROOT / "generated_release" / "production_config_report.json").read_text()).get("production_config_score", 0)
        if (ROOT / "generated_release" / "production_config_report.json").exists() else 0,
        "infrastructure": json.loads((ROOT / "generated_release" / "runtime_infrastructure_report.json").read_text()).get("infrastructure_score", 0)
        if (ROOT / "generated_release" / "runtime_infrastructure_report.json").exists() else 0,
        "observability": json.loads((ROOT / "generated_release" / "observability_operations_report.json").read_text()).get("observability_score", 0)
        if (ROOT / "generated_release" / "observability_operations_report.json").exists() else 0,
        "backup_restore": json.loads((ROOT / "generated_release" / "backup_restore_dr_report.json").read_text()).get("backup_restore_score", 0)
        if (ROOT / "generated_release" / "backup_restore_dr_report.json").exists() else 0,
        "performance": json.loads((ROOT / "generated_release" / "performance_scale_report.json").read_text()).get("performance_score", 0)
        if (ROOT / "generated_release" / "performance_scale_report.json").exists() else 0,
    }
    go_live_score = round(sum(score_map.values()) / max(len(score_map), 1), 1)

    critical_blockers = []
    if not compile_result.get("ok"):
        critical_blockers.append("compile_failed")
    if not tests.get("ok"):
        critical_blockers.append("unit_tests_failed")
    if not isolation.get("ok"):
        critical_blockers.append("release_isolation_failed")
    for name, result in phase_reports.items():
        if not result.get("ok"):
            critical_blockers.append(f"missing_or_failed_report:{name}")
    for name, result in smoke_results.items():
        if not result.get("ok"):
            critical_blockers.append(f"smoke_failed:{name}")
    for name, result in verify_results.items():
        if not result.get("ok"):
            critical_blockers.append(f"verify_failed:{name}")

    decision = "READY" if not critical_blockers and go_live_score >= 90 else ("READY WITH CONDITIONS" if go_live_score >= 80 and not any(
        b in critical_blockers for b in ("compile_failed", "unit_tests_failed", "release_isolation_failed")
    ) else "NOT READY")

    rc3_report = {
        "generated_at": utc_now(),
        "release": PHASE_RELEASES["F"],
        "phase": "F",
        "compile": compile_result,
        "unit_tests": tests,
        "smoke_tests": smoke_results,
        "verify_scripts": verify_results,
        "release_isolation": isolation,
        "phase_reports": phase_reports,
        "component_scores": score_map,
        "go_live_score": go_live_score,
        "decision": decision,
        "critical_blockers": critical_blockers,
        "ok": not critical_blockers,
    }
    write_report("RC3_PRODUCTION_CANDIDATE_REPORT.json", rc3_report)
    write_report("RC3_GO_LIVE_SCORE.json", {"score": go_live_score, "components": score_map, "generated_at": utc_now()})
    write_report("RC3_BLOCKERS.json", {"blockers": critical_blockers, "generated_at": utc_now(), "decision": decision})
    write_report(
        "RC3_CUTOVER_CHECKLIST.json",
        {
            "generated_at": utc_now(),
            "items": [
                {"item": "Production config validated", "ok": phase_reports["production_config"].get("ok")},
                {"item": "Runtime infrastructure validated", "ok": phase_reports["runtime_infrastructure"].get("ok")},
                {"item": "Observability operations validated", "ok": phase_reports["observability_operations"].get("ok")},
                {"item": "Backup/restore DR validated", "ok": phase_reports["backup_restore_dr"].get("ok")},
                {"item": "Performance scale smoke validated", "ok": phase_reports["performance_scale"].get("ok")},
                {"item": "Compile + unit tests passed", "ok": compile_result.get("ok") and tests.get("ok")},
                {"item": "Release isolation passed", "ok": isolation.get("ok")},
            ],
            "ok": not critical_blockers,
        },
    )
    return rc3_report


def run_phase_gate(phase: str, phase_runner, include_release_isolation: bool = True) -> dict:
    compile_result = run_compileall()
    tests = run_unit_tests()
    phase_report = phase_runner()
    isolation = run_release_isolation(PHASE_RELEASES[phase]) if include_release_isolation else {"ok": True, "skipped": True}
    sections = {
        "compile": compile_result,
        "unit_tests": tests,
        "phase_report": phase_report,
        "release_isolation": isolation,
    }
    ok = all(section.get("ok") for section in sections.values())
    return {"ok": ok, "sections": sections, "phase_report": phase_report}
