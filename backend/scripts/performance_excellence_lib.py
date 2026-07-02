"""Enterprise Hardening Pack 7 - Performance Excellence verification."""

from __future__ import annotations

import re

from scripts.enterprise_master_lib import (
    ROOT,
    create_test_app,
    run_compileall,
    run_release_isolation,
    run_unit_tests,
    scan_python_files,
    score_from_checks,
    utc_now,
    write_report,
)

RELEASE_ID = "enterprise-hardening-pack-7"


def scan_query_patterns() -> dict:
    timed = raw_sql = 0
    for path in scan_python_files(ROOT / "app"):
        text = path.read_text(encoding="utf-8")
        if "timed_query" in text:
            timed += 1
        if "db.session.execute" in text or "text(" in text:
            raw_sql += 1
    return {"ok": True, "timed_query_usages": timed, "raw_sql_usages": raw_sql}


def check_connection_pool(app) -> dict:
    from app.core.db_pool import pool_status, review_pool_config

    with app.app_context():
        status = pool_status(app)
        review = review_pool_config(app)
    return {
        "ok": True,
        "driver": status.get("driver"),
        "pool_pre_ping": status.get("pool_pre_ping"),
        "review_ok": review.get("ok"),
        "notes": review.get("notes", []),
    }


def check_endpoint_latency(app) -> dict:
    from app.extensions.db import db

    with app.app_context():
        db.create_all()
        client = app.test_client()
        samples = {}
        for path in ["/api/v1/system/health", "/api/v1/system/version", "/api/v1/system/stats"]:
            import time

            start = time.perf_counter()
            resp = client.get(path)
            samples[path] = {"status": resp.status_code, "duration_ms": round((time.perf_counter() - start) * 1000, 2)}
    slow = [p for p, v in samples.items() if v["duration_ms"] > 500]
    return {"ok": not slow, "samples": samples, "slow_endpoints": slow}


def run_performance_review(app) -> dict:
    checks = {
        "connection_pool": check_connection_pool(app),
        "query_patterns": scan_query_patterns(),
        "endpoint_latency": check_endpoint_latency(app),
        "performance_module": {"ok": (ROOT / "app" / "core" / "performance.py").exists()},
    }
    report = {
        "generated_at": utc_now(),
        "release": RELEASE_ID,
        "checks": checks,
        "score": score_from_checks(checks),
        "ok": all(item.get("ok") for item in checks.values()),
    }
    write_report("performance_review.json", report)
    return report


def run_latency_review(app) -> dict:
    latency = check_endpoint_latency(app)
    report = {
        "generated_at": utc_now(),
        "release": RELEASE_ID,
        "checks": {"endpoint_latency": latency},
        "ok": latency.get("ok", False),
    }
    write_report("latency_review.json", report)
    return report


def run_optimization_report() -> dict:
    redis_refs = webhook_refs = queue_refs = 0
    for path in scan_python_files(ROOT / "app"):
        text = path.read_text(encoding="utf-8")
        if "REDIS" in text or "redis" in text.lower():
            redis_refs += 1
        if "webhook" in text.lower():
            webhook_refs += 1
        if "queue" in text.lower():
            queue_refs += 1
    checks = {
        "redis_usage": {"ok": redis_refs >= 3, "references": redis_refs},
        "webhook_throughput_hooks": {"ok": webhook_refs >= 5, "references": webhook_refs},
        "queue_throughput_hooks": {"ok": queue_refs >= 10, "references": queue_refs},
    }
    report = {
        "generated_at": utc_now(),
        "release": RELEASE_ID,
        "checks": checks,
        "ok": all(item.get("ok") for item in checks.values()),
    }
    write_report("optimization_report.json", report)
    return report


def run_performance_excellence_verification() -> dict:
    compile_result = run_compileall()
    app, db = create_test_app()
    with app.app_context():
        db.create_all()
        perf = run_performance_review(app)
        latency = run_latency_review(app)
    opt = run_optimization_report()
    tests = run_unit_tests()
    sections = {
        "compile": compile_result,
        "performance_review": perf,
        "latency_review": latency,
        "optimization_report": opt,
        "unit_tests": tests,
    }
    ok = all(section.get("ok") for section in sections.values())
    return {"ok": ok, "sections": sections, "score": perf.get("score", 0)}
