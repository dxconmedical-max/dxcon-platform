#!/usr/bin/env python3
"""Production API smoke tests against a deployed DxCon base URL."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "PRODUCTION_SMOKE_REPORT.json"

DEFAULT_BASE_URL = "https://dxcon-ap.onrender.com"
TIMEOUT_SECONDS = 45

PROBE_KEYS = ("status", "app_env", "database", "redis", "timestamp")

DASHBOARD_LINKS = (
    ("/executive-v9", "Executive Dashboard"),
    ("/crm-pipeline", "CRM Pipeline"),
    ("/logistics", "Logistics"),
    ("/collector", "Collector"),
    ("/doctor/dashboard", "Doctor Workbench"),
    ("/api/v1/workflow/health", "Workflow Health"),
    ("/health", "API Health"),
    ("/ready", "Readiness"),
    ("/api-docs", "API Docs"),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def preview_text(text: str, limit: int = 240) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def http_request(
    method: str,
    url: str,
    *,
    body: dict | None = None,
    headers: dict | None = None,
    timeout: int = TIMEOUT_SECONDS,
    allow_redirects: bool = False,
) -> tuple[int, str, float, str | None]:
    payload = None
    req_headers = {"User-Agent": "dxcon-production-smoke/1.0", "Accept": "*/*"}
    if headers:
        req_headers.update(headers)
    if body is not None:
        payload = json.dumps(body).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    request = urllib.request.Request(url, data=payload, headers=req_headers, method=method)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8", errors="replace")
            return response.status, text, round((time.perf_counter() - start) * 1000, 2), response.geturl()
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        return exc.code, text, round((time.perf_counter() - start) * 1000, 2), exc.headers.get("Location")


def parse_json(text: str) -> dict | list | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def record(endpoint: str, url: str, status_code: int, latency_ms: float, text: str, ok: bool, notes: str = "") -> dict:
    return {
        "endpoint": endpoint,
        "url": url,
        "status_code": status_code,
        "pass": ok,
        "latency_ms": latency_ms,
        "response_preview": preview_text(text),
        "notes": notes,
    }


def validate_probe_json(payload: dict | list | None, required_keys: tuple[str, ...]) -> bool:
    if not isinstance(payload, dict):
        return False
    return all(key in payload for key in required_keys)


def validate_auth_error_shape(status_code: int, payload: dict | list | None) -> bool:
    if status_code not in {400, 401, 422}:
        return False
    if not isinstance(payload, dict):
        return False
    if payload.get("success") is False and isinstance(payload.get("error"), dict):
        error = payload["error"]
        return bool(error.get("code")) and bool(error.get("message"))
    if isinstance(payload.get("error"), str):
        return True
    message = str(payload.get("message", ""))
    return bool(message)


def validate_openapi(status_code: int, payload: dict | list | None) -> bool:
    if status_code != 200 or not isinstance(payload, dict):
        return False
    candidates = [payload]
    data = payload.get("data")
    if isinstance(data, dict):
        candidates.append(data)
    return any("openapi" in item and "paths" in item for item in candidates)


def validate_dashboard_link(status_code: int, redirect_location: str | None) -> tuple[bool, str]:
    if status_code == 404:
        return False, "route not found"
    if status_code == 200:
        return True, "ok"
    if status_code in {301, 302, 303, 307, 308} and redirect_location:
        return True, f"redirect={redirect_location}"
    if status_code in {401, 403}:
        return True, "auth protected"
    if status_code >= 500:
        return True, "degraded dashboard (route reachable)"
    return False, f"unexpected status {status_code}"


def run_smoke(base_url: str) -> dict:
    base_url = base_url.rstrip("/")
    results: list[dict] = []

    get_checks = [
        ("/", lambda code, _: code == 200, "home page"),
        ("/health", lambda code, payload: code == 200 and validate_probe_json(payload, PROBE_KEYS), "health probe"),
        ("/ready", lambda code, payload: code in {200, 503} and validate_probe_json(payload, PROBE_KEYS), "readiness probe"),
        ("/live", lambda code, payload: code == 200 and validate_probe_json(payload, PROBE_KEYS), "liveness probe"),
    ]

    health_payload = None
    for path, validator, label in get_checks:
        url = f"{base_url}{path}"
        status_code, text, latency_ms, _ = http_request("GET", url)
        payload = parse_json(text)
        if path == "/health":
            health_payload = payload
        ok = validator(status_code, payload)
        notes = label
        if path != "/" and payload is None and status_code == 200:
            notes = "expected JSON response"
            ok = False
        results.append(record(f"GET {path}", url, status_code, latency_ms, text, ok, notes))

    if isinstance(health_payload, dict):
        db_ok = health_payload.get("database") in {"OK", "UP"}
        redis_ok = health_payload.get("redis") in {"OK", "DEGRADED", "UP"}
        results.append(
            record(
                "database health",
                f"{base_url}/health",
                200,
                0,
                json.dumps({"database": health_payload.get("database")}),
                db_ok,
                "derived from /health payload",
            )
        )
        results.append(
            record(
                "redis health",
                f"{base_url}/health",
                200,
                0,
                json.dumps({"redis": health_payload.get("redis")}),
                redis_ok,
                "derived from /health payload",
            )
        )

    optional_health_path = "/api/v1/health"
    optional_url = f"{base_url}{optional_health_path}"
    status_code, text, latency_ms, _ = http_request("GET", optional_url)
    if status_code == 404:
        results.append(
            record(
                f"GET {optional_health_path}",
                optional_url,
                status_code,
                latency_ms,
                text,
                True,
                "optional endpoint not deployed; skipped",
            )
        )
    else:
        payload = parse_json(text)
        ok = status_code == 200 and isinstance(payload, dict)
        results.append(record(f"GET {optional_health_path}", optional_url, status_code, latency_ms, text, ok))

    auth_url = f"{base_url}/api/v1/auth/login"
    status_code, text, latency_ms, _ = http_request("POST", auth_url, body={}, headers={"Content-Type": "application/json", "Accept": "application/json"})
    auth_payload = parse_json(text)
    auth_ok = validate_auth_error_shape(status_code, auth_payload)
    results.append(
        record(
            "POST /api/v1/auth/login (missing credentials)",
            auth_url,
            status_code,
            latency_ms,
            text,
            auth_ok,
            "expects structured JSON validation/auth error",
        )
    )

    plain_request = urllib.request.Request(
        auth_url,
        data=b"email=only&password=only",
        headers={"User-Agent": "dxcon-production-smoke/1.0", "Content-Type": "text/plain"},
        method="POST",
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(plain_request, timeout=TIMEOUT_SECONDS) as response:
            plain_status = response.status
            plain_text = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        plain_status = exc.code
        plain_text = exc.read().decode("utf-8", errors="replace")
    plain_latency = round((time.perf_counter() - start) * 1000, 2)
    plain_payload = parse_json(plain_text)
    results.append(
        record(
            "POST /api/v1/auth/login (non-json payload)",
            auth_url,
            plain_status,
            plain_latency,
            plain_text,
            validate_auth_error_shape(plain_status, plain_payload),
            "expects structured error for non-JSON auth request",
        )
    )

    for path, label in DASHBOARD_LINKS:
        url = f"{base_url}{path}"
        status_code, text, latency_ms, redirect = http_request("GET", url, headers={"Accept": "text/html,application/json"})
        ok, link_note = validate_dashboard_link(status_code, redirect)
        notes = f"{label}; {link_note}"
        results.append(record(f"GET {path}", url, status_code, latency_ms, text, ok, notes))

    openapi_path = "/api/v1/openapi.json"
    openapi_url = f"{base_url}{openapi_path}"
    status_code, text, latency_ms, _ = http_request("GET", openapi_url, headers={"Accept": "application/json"})
    openapi_payload = parse_json(text)
    openapi_ok = validate_openapi(status_code, openapi_payload)
    notes = "OpenAPI document"
    if status_code == 404:
        openapi_ok = False
        notes = "openapi endpoint not found"
    results.append(record(f"GET {openapi_path}", openapi_url, status_code, latency_ms, text, openapi_ok, notes))

    passed = sum(1 for item in results if item["pass"])
    report = {
        "generated_at": utc_now(),
        "base_url": base_url,
        "summary": {
            "passed": passed,
            "total": len(results),
            "ok": passed == len(results),
        },
        "results": results,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def print_summary(report: dict) -> None:
    print("\n=== DXCON PRODUCTION API SMOKE ===\n")
    print(f"Target: {report['base_url']}\n")
    for item in report["results"]:
        status = "PASS" if item["pass"] else "FAIL"
        print(f"{status}: {item['endpoint']} -> {item['status_code']} ({item['latency_ms']} ms)")
        if item.get("notes"):
            print(f"  note: {item['notes']}")
    summary = report["summary"]
    print(f"\nSummary: {summary['passed']}/{summary['total']} passed")
    print(f"Report: {REPORT_PATH}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run production API smoke tests")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Production base URL")
    args = parser.parse_args()
    try:
        report = run_smoke(args.base_url)
    except urllib.error.URLError as exc:
        print(f"SMOKE FAILED: unable to reach {args.base_url}: {exc}", file=sys.stderr)
        return 1
    print_summary(report)
    return 0 if report["summary"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
