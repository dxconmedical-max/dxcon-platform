"""Shared helpers for Sprint 010.5 production readiness verification."""

from __future__ import annotations

import json
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated_release"
ENV_FILE = ROOT / ".env"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_database_url() -> str:
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "sqlite:///:memory:"


def is_postgresql(url: str) -> bool:
    return url.startswith("postgresql") or url.startswith("postgres")


def apply_migrations(db) -> None:
    for name in (
        "007_reporting_engine.sql",
        "008_portal.sql",
        "009_executive_platform.sql",
    ):
        path = ROOT / "migrations" / name
        if not path.exists():
            continue
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.strip().startswith("--")]
        for stmt in " ".join(lines).split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    db.session.execute(db.text(stmt))
                    db.session.commit()
                except Exception:
                    db.session.rollback()


def finding(status: str, name: str, detail: str = "", **extra) -> dict:
    return {"status": status, "name": name, "detail": detail, **extra}


def score_findings(findings: list[dict]) -> dict:
    counts = {"PASS": 0, "WARNING": 0, "FAIL": 0}
    for f in findings:
        counts[f.get("status", "FAIL")] = counts.get(f.get("status", "FAIL"), 0) + 1
    total = len(findings) or 1
    pct = round((counts["PASS"] + counts["WARNING"] * 0.5) / total * 100, 1)
    return {"counts": counts, "score_pct": pct, "total": len(findings)}


def write_report(name: str, payload: dict) -> Path:
    GENERATED.mkdir(parents=True, exist_ok=True)
    path = GENERATED / name
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def measure_ms(fn: Callable[[], Any]) -> tuple[Any, float]:
    start = time.perf_counter()
    result = fn()
    return result, (time.perf_counter() - start) * 1000


def concurrent_load(client_factory: Callable, path: str, workers: int, requests_per_worker: int = 3) -> dict:
    """Simulate concurrent users against a single endpoint."""
    latencies: list[float] = []
    errors = 0

    def _hit(_: int) -> float:
        client = client_factory()
        start = time.perf_counter()
        try:
            resp = client.get(path)
            if resp.status_code >= 500:
                return -1.0
            return (time.perf_counter() - start) * 1000
        except Exception:
            return -1.0

    with ThreadPoolExecutor(max_workers=min(workers, 32)) as pool:
        futures = [pool.submit(_hit, i) for i in range(workers * requests_per_worker)]
        for fut in as_completed(futures):
            ms = fut.result()
            if ms < 0:
                errors += 1
            else:
                latencies.append(ms)
    latencies.sort()
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 9999
    avg = sum(latencies) / len(latencies) if latencies else 9999
    return {"workers": workers, "requests": workers * requests_per_worker, "avg_ms": round(avg, 2), "p95_ms": round(p95, 2), "errors": errors}


def login_session(client, user) -> None:
    uid = user.id if hasattr(user, "id") else user.get("id")
    role = user.role if hasattr(user, "role") else user.get("role")
    email = user.email if hasattr(user, "email") else user.get("email")
    with client.session_transaction() as sess:
        sess["user_id"] = uid
        sess["role"] = role
        sess["email"] = email


def ensure_user(db, User, *, email: str, role: str) -> Any:
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, role=role, password_hash="x", is_active=True)
        db.session.add(user)
        db.session.commit()
    return user
