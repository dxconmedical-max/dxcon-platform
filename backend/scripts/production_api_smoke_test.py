#!/usr/bin/env python3
"""DxCon API edge smoke test — Release 8.1.

Usage:
    python backend/scripts/production_api_smoke_test.py
    python backend/scripts/production_api_smoke_test.py \\
        --api-base https://api-staging.dxcon.com.vn \\
        --cors-origin https://app-staging.dxcon.com.vn \\
        --denied-origin https://evil.attacker.example
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def fetch(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    timeout: float = 15.0,
) -> tuple[int, dict[str, str], str]:
    base_headers = {"User-Agent": "DxCon-APISmokeTest/8.1"}
    if headers:
        base_headers.update(headers)
    req = urllib.request.Request(url, method=method, headers=base_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, dict(resp.headers), body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, dict(exc.headers), body


def main() -> int:
    parser = argparse.ArgumentParser(description="DxCon API smoke test")
    parser.add_argument("--api-base", default="https://api.dxcon.com.vn")
    parser.add_argument("--cors-origin", default="https://app.dxcon.com.vn")
    parser.add_argument("--denied-origin", default="https://evil.attacker.example")
    parser.add_argument("--report", default="generated-release/API_EDGE_DIAGNOSTIC_REPORT.json")
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args()

    api_base = args.api_base.rstrip("/")
    results: list[dict] = []

    def check(name: str, passed: bool, detail: str = "", **extra) -> None:
        entry = {"name": name, "pass": passed, "detail": detail, **extra}
        results.append(entry)
        icon = "PASS" if passed else "FAIL"
        print(f"  [{icon}] {name}" + (f" — {detail}" if detail else ""))

    status, headers, body = fetch(f"{api_base}/api/v1/system/health", timeout=args.timeout)
    check(
        "api.health",
        status == 200,
        f"status={status}",
        server=headers.get("Server"),
        cf_ray=headers.get("CF-Ray"),
        acao=headers.get("Access-Control-Allow-Origin"),
    )
    if status == 403:
        check(
            "api.edge_not_blanket_403",
            False,
            "403 on public health — likely Cloudflare/WAF edge block",
            classification="EDGE_WAF",
        )
    else:
        check("api.edge_not_blanket_403", status != 403, f"status={status}")

    status, headers, _ = fetch(f"{api_base}/api/v1/auth/me", timeout=args.timeout)
    check("api.auth_rejection", status == 401, f"status={status}")

    status, headers, _ = fetch(
        f"{api_base}/api/v1/system/health",
        method="OPTIONS",
        headers={
            "Origin": args.cors_origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type,X-Organization-ID",
        },
        timeout=args.timeout,
    )
    acao = headers.get("Access-Control-Allow-Origin", "")
    check("api.cors_preflight", status in (200, 204) and acao == args.cors_origin, f"status={status} ACAO={acao}")

    status, headers, _ = fetch(
        f"{api_base}/api/v1/system/health",
        headers={"Origin": args.cors_origin},
        timeout=args.timeout,
    )
    check(
        "api.cors_allowed_origin",
        headers.get("Access-Control-Allow-Origin") == args.cors_origin,
        f"ACAO={headers.get('Access-Control-Allow-Origin')}",
    )

    status, headers, _ = fetch(
        f"{api_base}/api/v1/system/health",
        headers={"Origin": args.denied_origin},
        timeout=args.timeout,
    )
    check(
        "api.cors_denied_origin",
        not headers.get("Access-Control-Allow-Origin"),
        f"ACAO={headers.get('Access-Control-Allow-Origin') or '(none)'}",
    )

    for route in ["/api/v1/system/health", "/api/v1/system/version", "/api/v1/auth/me"]:
        status, _, _ = fetch(f"{api_base}{route}", timeout=args.timeout)
        check(f"api.no500{route}", status != 500, f"status={status}")

    passed = sum(1 for r in results if r["pass"])
    failed = sum(1 for r in results if not r["pass"])
    print(f"\nResults: {passed} passed, {failed} failed, {len(results)} total")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_base": api_base,
        "cors_origin": args.cors_origin,
        "denied_origin": args.denied_origin,
        "results": results,
        "summary": {"passed": passed, "failed": failed, "total": len(results)},
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Report written to {report_path}")

    if failed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
