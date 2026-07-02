"""Enterprise Hardening Pack 6 - Security Excellence verification."""

from __future__ import annotations

from scripts.enterprise_master_lib import (
    create_test_app,
    run_compileall,
    run_release_isolation,
    run_unit_tests,
    score_from_checks,
    utc_now,
    write_report,
)

RELEASE_ID = "enterprise-hardening-pack-6"


def run_security_review(app) -> dict:
    from app.core.security import SECURITY_HEADERS

    client = app.test_client()
    response = client.get("/api/v1/system/health")
    headers_ok = all(h in response.headers for h in SECURITY_HEADERS)
    checks = {
        "security_headers": {"ok": headers_ok, "count": len(SECURITY_HEADERS)},
        "jwt_configured": {"ok": bool(app.config.get("JWT_SECRET_KEY"))},
        "rate_limit_enabled": {"ok": bool(app.config.get("RATE_LIMIT_ENABLED"))},
        "cors_configured": {"ok": app.config.get("CORS_ORIGINS") is not None},
    }
    report = {
        "generated_at": utc_now(),
        "release": RELEASE_ID,
        "checks": checks,
        "score": score_from_checks(checks),
        "ok": all(item.get("ok") for item in checks.values()),
    }
    write_report("security_review.json", report)
    return report


def run_security_score(app) -> dict:
    from scripts.security_preflight_lib import run_security_preflight

    with app.app_context():
        from app.extensions.db import db

        db.create_all()
        preflight = run_security_preflight(app)
    passed = preflight.get("passed", 0)
    total = preflight.get("total", 1)
    score = round(100 * passed / total, 1) if total else 0
    report = {
        "generated_at": utc_now(),
        "release": RELEASE_ID,
        "score": score,
        "preflight": preflight,
        "ok": preflight.get("ok", False) or score >= 85,
    }
    write_report("security_score.json", report)
    return report


def run_vulnerability_review() -> dict:
    from scripts.security_preflight_lib import check_dependency_vulnerabilities

    deps = check_dependency_vulnerabilities()
    report = {
        "generated_at": utc_now(),
        "release": RELEASE_ID,
        "checks": {"dependency_vulnerabilities": deps},
        "ok": deps.get("ok", False),
    }
    write_report("vulnerability_review.json", report)
    return report


def run_security_excellence_verification() -> dict:
    compile_result = run_compileall()
    app, db = create_test_app()
    with app.app_context():
        db.create_all()
        review = run_security_review(app)
        score = run_security_score(app)
        vuln = run_vulnerability_review()
    tests = run_unit_tests()
    sections = {
        "compile": compile_result,
        "security_review": review,
        "security_score": score,
        "vulnerability_review": vuln,
        "unit_tests": tests,
    }
    ok = all(section.get("ok") for section in sections.values())
    return {"ok": ok, "sections": sections, "score": score.get("score", 0)}
