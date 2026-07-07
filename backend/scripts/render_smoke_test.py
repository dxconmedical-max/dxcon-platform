#!/usr/bin/env python3
"""Render smoke test (external HTTP).

Checks configured base URL endpoints for 200 OK.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated_release"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch(url: str, timeout_s: int = 10) -> dict:
    try:
        req = Request(url, headers={"User-Agent": "dxcon-render-smoke/1.0"})
        with urlopen(req, timeout=timeout_s) as resp:
            return {"ok": 200 <= resp.status < 300, "status": resp.status}
    except HTTPError as exc:
        return {"ok": False, "status": exc.code, "error": str(exc)}
    except URLError as exc:
        return {"ok": False, "status": None, "error": str(exc)}
    except Exception as exc:
        return {"ok": False, "status": None, "error": str(exc)}


def main() -> int:
    base = os.environ.get("RENDER_BASE_URL") or os.environ.get("BASE_URL") or ""
    if base.endswith("/"):
        base = base[:-1]

    endpoints = ["/", "/health", "/ready", "/login", "/app/executive"]
    results = {}

    findings = []
    if not base:
        findings.append({"status": "WARNING", "name": "base_url", "detail": "Set RENDER_BASE_URL to run external smoke"})
    else:
        findings.append({"status": "PASS", "name": "base_url", "detail": base})
        for ep in endpoints:
            res = fetch(f"{base}{ep}")
            results[ep] = res
            findings.append({
                "status": "PASS" if res.get("ok") else "FAIL",
                "name": f"http_{ep}",
                "detail": str(res),
            })

    report = {"generated_at": utc_now(), "base_url": base, "endpoints": endpoints, "results": results, "findings": findings}
    GENERATED.mkdir(parents=True, exist_ok=True)
    out = GENERATED / "RENDER_SMOKE_TEST_REPORT.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    fails = sum(1 for f in findings if f["status"] == "FAIL")
    print(f"Render smoke: {'PASS' if fails == 0 else 'FAIL'} ({out})")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

