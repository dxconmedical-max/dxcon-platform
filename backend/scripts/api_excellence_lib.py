"""Enterprise Hardening Pack 4 - API Excellence verification."""

from __future__ import annotations

import json
import re
from collections import defaultdict

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

RELEASE_ID = "enterprise-hardening-pack-4"


def scan_api_routes(app) -> dict:
    routes = []
    for rule in app.url_map.iter_rules():
        if str(rule.rule).startswith("/static"):
            continue
        methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
        routes.append({"path": str(rule.rule), "methods": methods, "endpoint": rule.endpoint})
    api_routes = [r for r in routes if r["path"].startswith("/api/")]
    return {"ok": len(api_routes) >= 200, "total": len(routes), "api_count": len(api_routes), "routes": api_routes}


def check_naming_consistency(routes: list) -> dict:
    bad = []
    for route in routes:
        path = route["path"]
        if not path.startswith("/api/v1/") and path.startswith("/api/"):
            bad.append(path)
    return {"ok": len(bad) <= 5, "non_v1_api_paths": bad[:20], "count": len(bad)}


def check_http_methods(routes: list) -> dict:
    allowed = {"GET", "POST", "PUT", "PATCH", "DELETE"}
    invalid = []
    for route in routes:
        extra = set(route["methods"]) - allowed
        if extra:
            invalid.append({"path": route["path"], "methods": route["methods"]})
    return {"ok": not invalid, "invalid": invalid[:10]}


def check_auth_decorators() -> dict:
    protected = routes = 0
    for path in scan_python_files(ROOT / "app" / "api"):
        text = path.read_text(encoding="utf-8")
        if "@jwt_required" in text or "require_permission" in text or "require_role" in text:
            protected += 1
        routes += text.count(".route(")
    return {"ok": protected >= 2 and routes >= 50, "files_with_auth_decorators": protected, "route_declarations": routes}


def check_openapi(app) -> dict:
    client = app.test_client()
    json_resp = client.get("/api/v1/openapi.json")
    yaml_resp = client.get("/api/v1/openapi.yaml")
    payload = {}
    if json_resp.status_code == 200:
        payload = json_resp.get_json() or {}
    return {
        "ok": json_resp.status_code == 200 and bool(payload.get("paths")),
        "json_status": json_resp.status_code,
        "yaml_status": yaml_resp.status_code,
        "path_count": len(payload.get("paths", {})),
        "openapi_version": payload.get("openapi"),
    }


def check_response_envelope(app) -> dict:
    client = app.test_client()
    health = client.get("/api/v1/system/health")
    payload = health.get_json() or {}
    envelope = "success" in payload
    legacy_health = payload.get("status") == "OK"
    return {
        "ok": health.status_code == 200 and (envelope or legacy_health),
        "status_code": health.status_code,
        "has_success": envelope,
        "legacy_health_ok": legacy_health,
    }


def check_error_schema(app) -> dict:
    client = app.test_client()
    bad = client.post("/api/v1/auth/login", data="not-json", content_type="application/json")
    payload = bad.get_json() or {}
    error = payload.get("error") or {}
    return {
        "ok": bad.status_code == 422 and error.get("code") == "VALIDATION_ERROR",
        "status_code": bad.status_code,
        "error_code": error.get("code"),
    }


def check_pagination_helpers() -> dict:
    hits = []
    for path in scan_python_files(ROOT / "app"):
        text = path.read_text(encoding="utf-8")
        if "get_list_params" in text or "ListParams" in text or "page=" in text:
            hits.append(str(path.relative_to(ROOT)))
    return {"ok": len(hits) >= 5, "files_with_pagination": len(hits), "sample": hits[:10]}


def run_api_review(app) -> dict:
    with app.app_context():
        routes_data = scan_api_routes(app)
        routes = [r for r in routes_data["routes"] if r["path"].startswith("/api/")]
        checks = {
            "route_inventory": routes_data,
            "naming_consistency": check_naming_consistency(routes),
            "http_methods": check_http_methods(routes),
            "auth_decorators": check_auth_decorators(),
            "response_envelope": check_response_envelope(app),
            "error_schema": check_error_schema(app),
            "pagination": check_pagination_helpers(),
        }
    report = {
        "generated_at": utc_now(),
        "release": RELEASE_ID,
        "checks": checks,
        "score": score_from_checks(checks),
        "ok": all(item.get("ok") for item in checks.values()),
    }
    write_report("api_review.json", report)
    return report


def run_openapi_validation(app) -> dict:
    openapi = check_openapi(app)
    report = {
        "generated_at": utc_now(),
        "release": RELEASE_ID,
        "checks": {"openapi": openapi},
        "ok": openapi.get("ok", False),
    }
    write_report("openapi_validation.json", report)
    return report


def run_api_consistency(app) -> dict:
    with app.app_context():
        routes_data = scan_api_routes(app)
        duplicates = defaultdict(list)
        for route in routes_data["routes"]:
            key = (route["path"], tuple(route["methods"]))
            duplicates[key].append(route["endpoint"])
        dupes = {str(k): v for k, v in duplicates.items() if len(v) > 1}
        checks = {
            "duplicate_routes": {"ok": not dupes, "count": len(dupes), "duplicates": dupes},
            "api_prefix": {"ok": routes_data["api_count"] >= 200, "api_routes": routes_data["api_count"]},
            "health_public": check_response_envelope(app),
        }
    report = {
        "generated_at": utc_now(),
        "release": RELEASE_ID,
        "checks": checks,
        "score": score_from_checks(checks),
        "ok": all(item.get("ok") for item in checks.values()),
    }
    write_report("api_consistency.json", report)
    return report


def run_api_excellence_verification() -> dict:
    compile_result = run_compileall()
    app, db = create_test_app()
    with app.app_context():
        db.create_all()
        review = run_api_review(app)
        openapi = run_openapi_validation(app)
        consistency = run_api_consistency(app)
    tests = run_unit_tests()
    sections = {
        "compile": compile_result,
        "api_review": review,
        "openapi_validation": openapi,
        "api_consistency": consistency,
        "unit_tests": tests,
    }
    ok = all(section.get("ok") for section in sections.values())
    return {"ok": ok, "sections": sections, "score": review.get("score", 0)}
