#!/usr/bin/env python3
"""Staging API smoke test — Release 9.0. No credentials required."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def fetch(url: str, *, method: str = "GET", headers: dict | None = None, timeout: float = 20.0):
    base = {"User-Agent": "DxCon-StagingAPISmoke/9.0"}
    if headers:
        base.update(headers)
    req = urllib.request.Request(url, method=method, headers=base)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read().decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", default="https://api-staging.dxcon.com.vn")
    parser.add_argument("--cors-origin", default="https://app-staging.dxcon.com.vn")
    parser.add_argument("--denied-origin", default="https://evil.attacker.example")
    parser.add_argument("--report", default="generated-release/STAGING_API_SMOKE_REPORT.json")
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()

    api = args.api_base.rstrip("/")
    results = []

    def check(name: str, ok: bool, detail: str = "", **extra):
        results.append({"name": name, "pass": ok, "detail": detail, **extra})
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    status, headers, _ = fetch(f"{api}/api/v1/system/health", timeout=args.timeout)
    check("api.health", status == 200, f"status={status}", server=headers.get("Server"), cf_ray=headers.get("CF-Ray"))
    check("api.no_blanket_edge_403", status != 403, f"status={status}")

    status, _, _ = fetch(f"{api}/api/v1/auth/me", timeout=args.timeout)
    check("api.auth_rejection", status in (401, 403), f"status={status}")

    status, headers, _ = fetch(
        f"{api}/api/v1/system/health",
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
        f"{api}/api/v1/system/health",
        headers={"Origin": args.cors_origin},
        timeout=args.timeout,
    )
    check("api.cors_allowed", headers.get("Access-Control-Allow-Origin") == args.cors_origin, f"ACAO={headers.get('Access-Control-Allow-Origin')}")

    status, headers, _ = fetch(
        f"{api}/api/v1/system/health",
        headers={"Origin": args.denied_origin},
        timeout=args.timeout,
    )
    check("api.cors_denied", not headers.get("Access-Control-Allow-Origin"), f"ACAO={headers.get('Access-Control-Allow-Origin') or '(none)'}")

    for route in ["/api/v1/system/health", "/api/v1/system/version", "/api/v1/auth/me"]:
        status, _, _ = fetch(f"{api}{route}", timeout=args.timeout)
        check(f"api.no500{route}", status != 500, f"status={status}")

    passed = sum(1 for r in results if r["pass"])
    failed = sum(1 for r in results if not r["pass"])
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_base": api,
        "cors_origin": args.cors_origin,
        "summary": {"passed": passed, "failed": failed, "total": len(results)},
        "results": results,
    }
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2))
    print(f"\nResults: {passed} passed, {failed} failed")
    print(f"Report: {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
