#!/usr/bin/env python3
"""DxCon Production API Smoke Test — Release 8.1 Sprint 9.

Verifies API health, auth rejection, CORS preflight, and no 500 on smoke routes.
No production credentials required.

Usage:
    python backend/scripts/production_api_smoke_test.py
    python backend/scripts/production_api_smoke_test.py \\
        --api-base https://api.uat.dxcon.com.vn \\
        --cors-origin https://app.uat.dxcon.com.vn
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone


def fetch(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    timeout: float = 15.0,
) -> tuple[int, dict[str, str], str]:
    req = urllib.request.Request(url, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, dict(resp.headers), body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, dict(exc.headers), body


def main() -> int:
    parser = argparse.ArgumentParser(description="DxCon production API smoke test")
    parser.add_argument(
        "--api-base",
        default="https://api.dxcon.com.vn",
        help="API base URL (default: https://api.dxcon.com.vn)",
    )
    parser.add_argument(
        "--cors-origin",
        default="https://app.dxcon.com.vn",
        help="Origin for CORS preflight test",
    )
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args()

    api_base = args.api_base.rstrip("/")
    results: list[dict] = []

    def check(name: str, passed: bool, detail: str = "") -> None:
        results.append({"name": name, "pass": passed, "detail": detail})
        icon = "PASS" if passed else "FAIL"
        print(f"  [{icon}] {name}" + (f" — {detail}" if detail else ""))

    # Health
    status, _, body = fetch(f"{api_base}/api/v1/system/health", timeout=args.timeout)
    check("api.health", status == 200, f"status={status}")

    # Auth rejection
    status, _, _ = fetch(f"{api_base}/api/v1/auth/me", timeout=args.timeout)
    check("api.auth_rejection", status == 401, f"status={status}")

    # CORS preflight
    status, headers, _ = fetch(
        f"{api_base}/api/v1/system/health",
        method="OPTIONS",
        headers={
            "Origin": args.cors_origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
        timeout=args.timeout,
    )
    acao = headers.get("Access-Control-Allow-Origin", "")
    cors_ok = status in (200, 204) and bool(acao)
    check("api.cors_preflight", cors_ok, f"status={status} ACAO={acao}")

    # No 500 on smoke routes
    for route in [
        "/api/v1/system/health",
        "/api/v1/system/version",
        "/api/v1/auth/me",
        "/api/v1/auth/login",
    ]:
        status, _, _ = fetch(f"{api_base}{route}", timeout=args.timeout)
        check(f"api.no500{route}", status != 500, f"status={status}")

    passed = sum(1 for r in results if r["pass"])
    failed = sum(1 for r in results if not r["pass"])
    print(f"\nResults: {passed} passed, {failed} failed, {len(results)} total")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_base": api_base,
        "cors_origin": args.cors_origin,
        "results": results,
        "summary": {"passed": passed, "failed": failed, "total": len(results)},
    }
    report_path = "generated-release/PRODUCTION_API_SMOKE_REPORT.json"
    try:
        with open(report_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print(f"Report written to {report_path}")
    except OSError as exc:
        print(f"Warning: could not write report: {exc}", file=sys.stderr)

    if failed:
        print("\nFailed checks:")
        for r in results:
            if not r["pass"]:
                print(f"  - {r['name']}: {r['detail']}")
        return 1
    print("\nAll API smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
