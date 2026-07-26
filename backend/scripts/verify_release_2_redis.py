#!/usr/bin/env python3
"""Release 2 Redis verification — environment-aware (never print credentials).

Outside Render private network:
  - Do NOT resolve or connect to internal red-* hostnames.
  - Local DNS / TCP / PING against REDIS_URL → NOT APPLICABLE.
  - Verify indirectly via production HTTP readiness/health endpoints.

Inside Render (RENDER=true or DXCON_REDIS_DIRECT=1):
  - Initialize redis client from REDIS_URL and PING (credentials never printed).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated_release"
DEFAULT_API = "https://api.dxcon.com.vn"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def on_render_runtime() -> bool:
    if os.environ.get("DXCON_REDIS_DIRECT", "").strip() in {"1", "true", "yes"}:
        return True
    return bool(os.environ.get("RENDER") or os.environ.get("RENDER_SERVICE_ID"))


def sanitize(text: str) -> str:
    text = re.sub(r"redis(?:s)?://[^\s\"']+", "redis://***", text, flags=re.I)
    text = re.sub(r"(?i)://[^:\s/]+:[^@\s/]+@", "://***:***@", text)
    text = re.sub(r"\bred-[A-Za-z0-9]+\b", "red-***", text)
    return text


def redact_host(host: str | None) -> str | None:
    if not host:
        return None
    if host.startswith("red-"):
        return "red-***"
    if "." in host:
        parts = host.split(".")
        return parts[0][:4] + "***." + ".".join(parts[1:])
    return host[:3] + "***"


def host_class(host: str | None) -> str:
    if not host:
        return "missing"
    if re.fullmatch(r"red-x+", host, flags=re.I):
        return "placeholder_x"
    if re.fullmatch(r"red-[a-z0-9]+", host, flags=re.I):
        return "render_internal"
    if host in {"localhost", "127.0.0.1", "redis"}:
        return "local_dev"
    return "other"


def is_render_internal_host(host: str | None) -> bool:
    return bool(host) and host.lower().startswith("red-")


def http_get(url: str, timeout: float = 40.0) -> tuple[int | None, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "dxcon-verify-release-2-redis/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as resp:
            raw = resp.read().decode("utf-8", "replace")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, {"_raw": sanitize(raw[:500])}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"_raw": sanitize(raw[:500])}
    except Exception as exc:  # noqa: BLE001 — verifier must never crash on probe errors
        return None, {"_error": sanitize(f"{type(exc).__name__}: {exc}")}


def extract_redis_check(health: dict) -> dict:
    data = health.get("data") if isinstance(health, dict) else None
    if not isinstance(data, dict):
        return {}
    startup = data.get("startup") or {}
    checks = startup.get("checks") or []
    for item in checks:
        if isinstance(item, dict) and item.get("name") == "redis":
            return item
    return {}


def extract_scheduler_check(health: dict) -> dict:
    data = health.get("data") if isinstance(health, dict) else None
    if not isinstance(data, dict):
        return {}
    startup = data.get("startup") or {}
    checks = startup.get("checks") or []
    for item in checks:
        if isinstance(item, dict) and item.get("name") == "scheduler":
            return item
    return {}


def host_from_error_detail(detail: str) -> str | None:
    match = re.search(r"connecting to ([^:\s]+):(\d+)", detail or "")
    return match.group(1) if match else None


def verify_outside_render(api_base: str) -> dict:
    """Indirect verification only — never DNS/TCP/PING internal red-* hosts."""
    health_code, health = http_get(f"{api_base.rstrip('/')}/api/v1/system/health")
    root_health_code, root_health = http_get(f"{api_base.rstrip('/')}/health")
    ready_code, ready = http_get(f"{api_base.rstrip('/')}/api/v1/system/ready")
    workers_code, workers = http_get(f"{api_base.rstrip('/')}/api/v1/system/workers")
    mon_code, mon = http_get(f"{api_base.rstrip('/')}/api/v1/monitoring-center/redis")

    redis_check = extract_redis_check(health if isinstance(health, dict) else {})
    scheduler_check = extract_scheduler_check(health if isinstance(health, dict) else {})
    detail = sanitize(str(redis_check.get("detail") or ""))
    err_host = host_from_error_detail(redis_check.get("detail") or "")
    cfg = ((health.get("data") or {}).get("startup") or {}).get("config") if isinstance(health, dict) else {}
    build = (health.get("data") or {}).get("build") if isinstance(health, dict) else {}

    redis_status = redis_check.get("status")
    if redis_status == "pass":
        api_redis = "PASS"
    elif redis_status == "fail":
        api_redis = "FAIL"
    elif redis_status in {"skipped", "warn"}:
        api_redis = "NOT VERIFIED"
    else:
        api_redis = "NOT VERIFIED"

    root_redis = None
    if isinstance(root_health, dict):
        root_redis = root_health.get("redis")

    # Dedicated worker Redis evidence is not exposed unless workers endpoint succeeds
    # with an explicit redis/broker field. In-process scheduler ≠ Redis broker.
    worker_redis = "NOT VERIFIED"
    if workers_code == 200 and isinstance(workers, dict):
        payload = workers.get("data") if isinstance(workers.get("data"), dict) else workers
        if isinstance(payload, dict) and any(k in payload for k in ("redis", "broker", "redis_ok")):
            flag = payload.get("redis_ok")
            if flag is True or payload.get("redis") in {"OK", "pass", "connected"}:
                worker_redis = "PASS"
            elif flag is False or payload.get("redis") in {"FAIL", "fail", "DOWN", "DEGRADED"}:
                worker_redis = "FAIL"

    scheduler_redis = "NOT VERIFIED"
    if scheduler_check.get("status") == "pass":
        # In-process background workers — not evidence of Redis broker connectivity
        scheduler_redis = "NOT VERIFIED"

    mon_ping = None
    if isinstance(mon, dict) and isinstance(mon.get("data"), dict):
        mon_ping = mon["data"].get("ping")

    return {
        "mode": "outside_render_indirect",
        "local_dns_check": "NOT APPLICABLE",
        "local_tcp_check": "NOT APPLICABLE",
        "local_redis_ping": "NOT APPLICABLE",
        "note": (
            "Render internal red-* hostnames must not be resolved from Mac, CI, "
            "Vercel, or other non-Render networks. Use HTTP readiness or in-Render PING."
        ),
        "api_base": api_base,
        "sanitized_hostname": redact_host(err_host) if err_host else None,
        "hostname_class": host_class(err_host) if err_host else None,
        "api_redis": api_redis,
        "worker_redis": worker_redis,
        "scheduler_redis": scheduler_redis,
        "probes": {
            "system_health_http": health_code,
            "root_health_http": root_health_code,
            "system_ready_http": ready_code,
            "workers_http": workers_code,
            "monitoring_redis_http": mon_code,
            "redis_startup_check": {
                "status": redis_check.get("status"),
                "detail": detail,
            },
            "scheduler_startup_check": {
                "status": scheduler_check.get("status"),
                "workers": scheduler_check.get("workers"),
            },
            "root_health_redis": root_redis,
            "root_health_status": root_health.get("status") if isinstance(root_health, dict) else None,
            "redis_configured": (cfg or {}).get("redis_configured"),
            "app_env": (cfg or {}).get("app_env"),
            "build": build,
            "monitoring_ping_status": (mon_ping or {}).get("status") if isinstance(mon_ping, dict) else None,
            "monitoring_ping_mode": (mon_ping or {}).get("mode") if isinstance(mon_ping, dict) else None,
            "monitoring_ping_error": sanitize(str((mon_ping or {}).get("error") or ""))
            if isinstance(mon_ping, dict)
            else None,
        },
    }


def verify_inside_render() -> dict:
    """Direct REDIS_URL PING — only safe on Render private network."""
    url = (os.environ.get("REDIS_URL") or "").strip()
    parsed = urlparse(url) if url else None
    host = parsed.hostname if parsed else None
    port = parsed.port or 6379
    result: dict[str, Any] = {
        "mode": "inside_render_direct",
        "local_dns_check": "APPLICABLE",
        "sanitized_hostname": redact_host(host),
        "hostname_class": host_class(host),
        "port": port,
        "scheme": parsed.scheme if parsed else None,
    }
    if not url:
        result.update(
            {
                "api_redis": "FAIL",
                "worker_redis": "NOT VERIFIED",
                "scheduler_redis": "NOT VERIFIED",
                "detail": "REDIS_URL missing",
            }
        )
        return result

    # DNS inside Render only
    try:
        socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        result["dns"] = "PASS"
    except OSError as exc:
        result["dns"] = "FAIL"
        result["dns_error"] = sanitize(str(exc))

    try:
        import redis
    except ImportError:
        result.update(
            {
                "api_redis": "NOT VERIFIED",
                "worker_redis": "NOT VERIFIED",
                "scheduler_redis": "NOT VERIFIED",
                "detail": "redis package not installed",
            }
        )
        return result

    try:
        client = redis.from_url(url, socket_connect_timeout=2)
        client.ping()
        result["ping"] = "PASS"
        result["api_redis"] = "PASS"
        # Same process role may be api/worker/scheduler via DXCON_PROCESS_ROLE
        role = (os.environ.get("DXCON_PROCESS_ROLE") or "api").lower()
        result["worker_redis"] = "PASS" if role == "worker" else "NOT VERIFIED"
        result["scheduler_redis"] = "PASS" if role == "scheduler" else "NOT VERIFIED"
        if role == "api":
            # Direct PING success proves Redis reachable for this runtime; worker/scheduler
            # still need their own services or explicit role evidence.
            pass
        result["detail"] = "PING OK"
    except Exception as exc:  # noqa: BLE001
        result["ping"] = "FAIL"
        result["api_redis"] = "FAIL"
        result["worker_redis"] = "NOT VERIFIED"
        result["scheduler_redis"] = "NOT VERIFIED"
        result["detail"] = sanitize(str(exc))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Release 2 environment-aware Redis verification")
    parser.add_argument("--api-base", default=os.environ.get("DXCON_API_BASE", DEFAULT_API))
    parser.add_argument("--json-out", default=str(GENERATED / "RELEASE_2_REDIS_VERIFY.json"))
    args = parser.parse_args(argv)

    if on_render_runtime():
        payload = verify_inside_render()
    else:
        # Explicitly refuse local direct connect to red-* even if REDIS_URL is present
        env_url = (os.environ.get("REDIS_URL") or "").strip()
        env_host = urlparse(env_url).hostname if env_url else None
        payload = verify_outside_render(args.api_base)
        if env_url and is_render_internal_host(env_host):
            payload["refused_local_direct"] = {
                "reason": "REDIS_URL points at Render internal host; local DNS/TCP/PING skipped",
                "sanitized_hostname": redact_host(env_host),
            }

    payload["timestamp"] = utc_now()
    payload["go_live"] = "NOT PASS"
    # Layer rollup: do not mark entire Redis FAIL if only some roles lack evidence
    statuses = [payload.get("api_redis"), payload.get("worker_redis"), payload.get("scheduler_redis")]
    if payload.get("api_redis") == "PASS" and all(s in {"PASS", "NOT VERIFIED"} for s in statuses):
        payload["redis_layer"] = "PARTIAL" if "NOT VERIFIED" in statuses else "PASS"
    elif payload.get("api_redis") == "FAIL":
        payload["redis_layer"] = "API_FAIL_OTHERS_SEPARATE"
    else:
        payload["redis_layer"] = "NOT VERIFIED"

    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print("Release 2 Redis verification")
    print(f"  mode: {payload.get('mode')}")
    print(f"  local_dns_check: {payload.get('local_dns_check')}")
    print(f"  sanitized_hostname: {payload.get('sanitized_hostname')}")
    print(f"  hostname_class: {payload.get('hostname_class')}")
    print(f"  API Redis: {payload.get('api_redis')}")
    print(f"  Worker Redis: {payload.get('worker_redis')}")
    print(f"  Scheduler Redis: {payload.get('scheduler_redis')}")
    print(f"  redis_layer: {payload.get('redis_layer')}")
    print(f"  go_live: {payload.get('go_live')}")
    print(f"  wrote: {out}")

    # Non-zero only when API Redis explicitly FAIL (worker/scheduler NOT VERIFIED is OK)
    return 1 if payload.get("api_redis") == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
