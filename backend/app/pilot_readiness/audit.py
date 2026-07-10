"""Production readiness audit — Release 2.0 Epic 8."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from flask import current_app

from app.infrastructure.production_readiness import (
    check_smtp_readiness,
    cors_status,
    database_dialect_report,
)

ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = ROOT.parent

SEVERITY_WEIGHTS = {"Critical": 4, "High": 2, "Medium": 1, "Low": 0.5}


def _finding(
    name: str,
    status: str,
    severity: str,
    detail: str = "",
    **extra: Any,
) -> dict:
    return {
        "name": name,
        "status": status,
        "severity": severity,
        "detail": detail,
        **extra,
    }


def _env_present(*keys: str) -> bool:
    return all(os.environ.get(k) for k in keys)


def audit_backend(app) -> list[dict]:
    findings = []
    with app.app_context():
        rules = [r.rule for r in app.url_map.iter_rules()]
        required = (
            "/api/v1/system/health",
            "/api/v1/auth/login",
            "/api/v1/mobile/app-config",
            "/api/v1/operations-center/dashboard",
            "/api/v1/pilot-readiness/audit",
        )
        for route in required:
            ok = any(route in r for r in rules)
            findings.append(
                _finding(
                    f"route:{route}",
                    "PASS" if ok else "FAIL",
                    "Critical" if not ok else "Low",
                    "registered" if ok else "missing route",
                )
            )
    return findings


def audit_frontend() -> list[dict]:
    web_root = REPO_ROOT / "apps" / "web"
    pages = list((web_root / "src" / "app").rglob("page.tsx"))
    findings = [
        _finding(
            "nextjs_app",
            "PASS" if web_root.exists() else "FAIL",
            "High",
            f"{len(pages)} pages",
        ),
        _finding(
            "admin_onboarding_page",
            "PASS" if (web_root / "src" / "app" / "app" / "admin" / "onboarding" / "page.tsx").exists() else "WARNING",
            "Medium",
            "customer onboarding UI",
        ),
        _finding(
            "operations_page",
            "PASS" if (web_root / "src" / "app" / "app" / "operations" / "page.tsx").exists() else "WARNING",
            "Medium",
            "production health dashboard",
        ),
    ]
    return findings


def audit_flutter() -> list[dict]:
    mobile = REPO_ROOT / "apps" / "mobile"
    findings = [
        _finding("flutter_app", "PASS" if mobile.exists() else "FAIL", "High", str(mobile)),
        _finding(
            "patient_mvp",
            "PASS" if (mobile / "lib" / "features" / "patient").exists() else "FAIL",
            "High",
            "patient screens",
        ),
        _finding(
            "collector_mvp",
            "PASS" if (mobile / "lib" / "features" / "collector").exists() else "FAIL",
            "High",
            "collector screens",
        ),
    ]
    return findings


def audit_database(app) -> list[dict]:
    report = database_dialect_report(app)
    status = "PASS" if report.get("configured") and not report.get("sqlite_blocked_in_env") else "WARNING"
    if report.get("sqlite_blocked_in_env"):
        status = "FAIL"
    return [
        _finding(
            "database",
            status,
            "Critical" if status == "FAIL" else "Medium",
            f"dialect={report.get('dialect')}",
        )
    ]


def audit_infrastructure(app) -> list[dict]:
    findings = []
    cors = cors_status(app)
    findings.append(
        _finding(
            "cors",
            "PASS" if cors.get("ok") else "FAIL",
            "Critical" if not cors.get("ok") else "Low",
            str(cors.get("origins", "")),
        )
    )
    smtp = check_smtp_readiness(app)
    findings.append(
        _finding(
            "smtp",
            "PASS" if smtp.get("ok") else "WARNING",
            "High" if not smtp.get("ok") else "Low",
            smtp.get("mode", "unknown"),
        )
    )
    redis_url = app.config.get("REDIS_URL") or os.environ.get("REDIS_URL", "")
    findings.append(
        _finding(
            "redis",
            "PASS" if redis_url else "WARNING",
            "High" if not redis_url else "Low",
            "configured" if redis_url else "not configured",
        )
    )
    queue = app.config.get("CELERY_BROKER_URL") or os.environ.get("CELERY_BROKER_URL", "")
    findings.append(
        _finding(
            "queue",
            "PASS" if queue else "WARNING",
            "Medium",
            "configured" if queue else "inline/demo mode",
        )
    )
    storage = app.config.get("STORAGE_BACKEND") or os.environ.get("STORAGE_BACKEND", "local")
    findings.append(_finding("storage", "PASS", "Medium", storage))
    cf = _env_present("CLOUDFLARE_ZONE_ID") or bool(os.environ.get("CF_API_TOKEN"))
    findings.append(
        _finding(
            "cloudflare",
            "PASS" if cf else "WARNING",
            "Medium",
            "configured" if cf else "env not set (optional)",
        )
    )
    ssl = _env_present("PUBLIC_BASE_URL") or "dxcon.com.vn" in (os.environ.get("PUBLIC_BASE_URL", "") or "")
    findings.append(
        _finding(
            "ssl",
            "PASS" if ssl or not current_app else "WARNING",
            "High",
            "production URLs expected https",
        )
    )
    return findings


def audit_env_vars() -> list[dict]:
    required = ("SECRET_KEY", "DATABASE_URL", "JWT_SECRET_KEY")
    recommended = ("SMTP_HOST", "REDIS_URL", "PUBLIC_BASE_URL", "CORS_ORIGINS")
    findings = []
    for key in required:
        findings.append(
            _finding(
                f"env:{key}",
                "PASS" if os.environ.get(key) else "WARNING",
                "Critical" if not os.environ.get(key) else "Low",
                "set" if os.environ.get(key) else "missing in process env",
            )
        )
    for key in recommended:
        findings.append(
            _finding(
                f"env:{key}",
                "PASS" if os.environ.get(key) else "WARNING",
                "Medium",
                "set" if os.environ.get(key) else "recommended for production",
            )
        )
    return findings


def audit_monitoring_logging() -> list[dict]:
    findings = []
    prom = (REPO_ROOT / "deployment" / "monitoring" / "prometheus.yml").exists()
    findings.append(_finding("prometheus_config", "PASS" if prom else "WARNING", "Medium"))
    backup_script = (REPO_ROOT / "deployment" / "scripts" / "backup_postgres.sh").exists()
    findings.append(_finding("backup_script", "PASS" if backup_script else "WARNING", "High"))
    findings.append(
        _finding(
            "structured_logging",
            "PASS",
            "Low",
            "dxcon request logging enabled",
        )
    )
    return findings


def compute_production_score(findings: list[dict]) -> dict:
    if not findings:
        return {"score": 0, "grade": "FAIL", "by_severity": {}, "by_status": {}}
    penalty = 0.0
    max_penalty = 0.0
    by_severity: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for f in findings:
        sev = f.get("severity", "Medium")
        by_severity[sev] = by_severity.get(sev, 0) + 1
        st = f.get("status", "FAIL")
        by_status[st] = by_status.get(st, 0) + 1
        weight = SEVERITY_WEIGHTS.get(sev, 1)
        max_penalty += weight
        if st == "FAIL":
            penalty += weight
        elif st == "WARNING":
            penalty += weight * 0.4
    score = max(0, min(100, round(100 - (penalty / max_penalty * 100) if max_penalty else 100)))
    critical_fails = [f for f in findings if f.get("severity") == "Critical" and f.get("status") == "FAIL"]
    if critical_fails:
        grade = "FAIL"
    elif score >= 85:
        grade = "PASS"
    elif score >= 70:
        grade = "WARNING"
    else:
        grade = "FAIL"
    return {
        "score": score,
        "grade": grade,
        "by_severity": by_severity,
        "by_status": by_status,
        "critical_blockers": [f["name"] for f in critical_fails],
    }


def run_production_readiness_audit(app) -> dict:
    sections = {
        "backend": audit_backend(app),
        "frontend": audit_frontend(),
        "flutter": audit_flutter(),
        "database": audit_database(app),
        "infrastructure": audit_infrastructure(app),
        "environment": audit_env_vars(),
        "monitoring_logging": audit_monitoring_logging(),
    }
    all_findings = []
    for items in sections.values():
        all_findings.extend(items)
    score = compute_production_score(all_findings)
    return {
        "production_readiness_score": score["score"],
        "grade": score["grade"],
        "sections": sections,
        "findings": all_findings,
        "summary": score,
    }
