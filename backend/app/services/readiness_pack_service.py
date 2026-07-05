"""Readiness pack business logic for Phase 5 Sprint 5.14."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.services.monitoring_center_service import application_health, database_health, redis_health
from app.services.production_deployment_service import health_probes, release_checklist
from app.services.release_management_service import migration_status, release_health
from app.web.demo_pilot_lib import seeded_summary, system_status

READINESS_PACK_ROLES = ("SUPER_ADMIN", "ADMIN")

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
GENERATED = ROOT / "generated_release"

READINESS_ASSETS = {
    "system_report": GENERATED / "SYSTEM_READINESS_REPORT.json",
    "security_report": GENERATED / "SECURITY_READINESS_REPORT.json",
    "pilot_report": GENERATED / "PILOT_READINESS_REPORT.json",
    "go_live_checklist": GENERATED / "GO_LIVE_CHECKLIST.json",
    "known_limitations": REPO / "docs" / "KNOWN_LIMITATIONS.md",
    "roadmap_v2": REPO / "docs" / "ROADMAP_v2.md",
}

FEATURES = (
    "SYSTEM_READINESS_REPORT.json",
    "SECURITY_READINESS_REPORT.json",
    "PILOT_READINESS_REPORT.json",
    "GO_LIVE_CHECKLIST.json",
    "KNOWN_LIMITATIONS.md",
    "ROADMAP_v2.md",
)


def ensure_readiness_pack() -> dict[str, Any]:
    return {"ready": True, "read_only": True}


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_doc(path: Path) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    sections = [line.lstrip("#").strip() for line in content.splitlines() if line.startswith("## ")]
    return {
        "path": str(path.relative_to(REPO)) if path.exists() else str(path),
        "exists": path.exists(),
        "sections": sections,
        "content": content,
        "size_bytes": len(content.encode("utf-8")),
    }


def system_readiness_report() -> dict[str, Any]:
    ensure_readiness_pack()
    stored = _load_json(READINESS_ASSETS["system_report"])
    app = application_health()
    db = database_health()
    redis = redis_health()
    health = release_health()
    probes = health_probes()
    migration = migration_status()
    status_probe = system_status()
    seed = seeded_summary()

    checks = [
        {"name": "application_health", "status": app.get("status"), "ok": app.get("status") == "OK"},
        {"name": "database_health", "status": db.get("status"), "ok": db.get("connectivity") == "OK"},
        {"name": "redis_health", "status": redis.get("status"), "ok": redis.get("status") in ("OK", "DEGRADED")},
        {"name": "release_health", "status": health["health"]["payload"].get("status"), "ok": health["live"]["status_code"] == 200},
        {"name": "migration", "status": migration.get("status"), "ok": migration.get("status") == "READY"},
        {"name": "health_probes", "status": "OK" if probes.get("checks_passed", 0) >= probes.get("checks_total", 1) - 1 else "WARN", "ok": probes.get("checks_passed", 0) > 0},
    ]
    passed = sum(1 for item in checks if item["ok"])
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0

    live = {
        "report": "system_readiness_report",
        "read_only": True,
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "5.14",
        "sprint": "Readiness Pack",
        "summary": {
            "score": score,
            "checks_passed": passed,
            "checks_total": total,
            "ok": passed == total,
            "system_status": status_probe.get("status"),
            "database": status_probe.get("database"),
            "redis": status_probe.get("redis"),
        },
        "checks": {item["name"]: item for item in checks},
        "seeded_summary": seed,
        "health_probes": probes,
        "migration": migration,
        "stored_report_available": stored is not None,
        "stored_report_generated_at": (stored or {}).get("generated_at"),
    }
    if stored:
        live["stored_summary"] = stored.get("summary")
    return live


def security_readiness_report() -> dict[str, Any]:
    ensure_readiness_pack()
    payload = _load_json(READINESS_ASSETS["security_report"]) or {}
    return {
        "report": "security_readiness_report",
        "read_only": True,
        "filename": "SECURITY_READINESS_REPORT.json",
        "exists": READINESS_ASSETS["security_report"].exists(),
        "phase": payload.get("phase"),
        "sprint": payload.get("sprint"),
        "summary": payload.get("summary", {}),
        "checks_count": len(payload.get("checks", {})),
        "payload": payload,
    }


def pilot_readiness_report() -> dict[str, Any]:
    ensure_readiness_pack()
    payload = _load_json(READINESS_ASSETS["pilot_report"]) or {}
    return {
        "report": "pilot_readiness_report",
        "read_only": True,
        "filename": "PILOT_READINESS_REPORT.json",
        "exists": READINESS_ASSETS["pilot_report"].exists(),
        "summary": payload.get("summary", {}),
        "checks": payload.get("checks", {}),
        "payload": payload,
    }


def go_live_checklist_report() -> dict[str, Any]:
    ensure_readiness_pack()
    stored = _load_json(READINESS_ASSETS["go_live_checklist"])
    checklist = release_checklist()
    items = checklist.get("items", [])
    if stored and stored.get("items"):
        items = stored["items"]
    checked = sum(1 for item in items if item.get("checked"))
    return {
        "report": "go_live_checklist_report",
        "read_only": True,
        "filename": "GO_LIVE_CHECKLIST.json",
        "exists": READINESS_ASSETS["go_live_checklist"].exists() or bool(items),
        "items": items,
        "items_total": len(items),
        "items_checked": checked,
        "items_remaining": len(items) - checked,
        "verify_scripts": checklist.get("verify_scripts", []),
        "deployment_current": checklist.get("deployment_current"),
        "legacy_route": "/pilot-checklist",
    }


def known_limitations_doc() -> dict[str, Any]:
    ensure_readiness_pack()
    doc = _read_doc(READINESS_ASSETS["known_limitations"])
    doc["report"] = "known_limitations"
    doc["read_only"] = True
    doc["filename"] = "KNOWN_LIMITATIONS.md"
    return doc


def roadmap_v2_doc() -> dict[str, Any]:
    ensure_readiness_pack()
    doc = _read_doc(READINESS_ASSETS["roadmap_v2"])
    doc["report"] = "roadmap_v2"
    doc["read_only"] = True
    doc["filename"] = "ROADMAP_v2.md"
    return doc


def readiness_pack_inventory() -> dict[str, Any]:
    ensure_readiness_pack()
    items = []
    for key, path in (
        ("system", READINESS_ASSETS["system_report"]),
        ("security", READINESS_ASSETS["security_report"]),
        ("pilot", READINESS_ASSETS["pilot_report"]),
        ("go_live_checklist", READINESS_ASSETS["go_live_checklist"]),
        ("known_limitations", READINESS_ASSETS["known_limitations"]),
        ("roadmap_v2", READINESS_ASSETS["roadmap_v2"]),
    ):
        items.append(
            {
                "key": key,
                "filename": path.name,
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
            }
        )
    missing = [item["filename"] for item in items if not item["exists"]]
    return {
        "report": "readiness_pack_inventory",
        "read_only": True,
        "artifacts_total": len(items),
        "artifacts_present": len(items) - len(missing),
        "missing": missing,
        "items": items,
    }


def readiness_pack_dashboard() -> dict[str, Any]:
    ensure_readiness_pack()
    system = system_readiness_report()
    security = security_readiness_report()
    pilot = pilot_readiness_report()
    checklist = go_live_checklist_report()
    limitations = known_limitations_doc()
    roadmap = roadmap_v2_doc()
    inventory = readiness_pack_inventory()

    status = "OK"
    if not security["exists"] or not pilot["exists"]:
        status = "WARN"
    if system["summary"]["score"] < 80:
        status = "WARN"
    if inventory["missing"]:
        status = "WARN"

    return {
        "report": "readiness_pack_dashboard",
        "read_only": True,
        "status": status,
        "system_score": system["summary"]["score"],
        "security_score": security.get("summary", {}).get("score"),
        "pilot_score": pilot.get("summary", {}).get("pilot_readiness_score"),
        "checklist_remaining": checklist["items_remaining"],
        "artifacts_present": inventory["artifacts_present"],
    }


def readiness_pack_readiness_report() -> dict[str, Any]:
    dashboard = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "5.14",
        "sprint": "Readiness Pack",
        "platform": dashboard["platform"],
        "status": dashboard["status"],
        "summary": dashboard["summary"],
        "features": list(FEATURES),
        "sections": {
            "system": system_readiness_report(),
            "security": security_readiness_report(),
            "pilot": pilot_readiness_report(),
            "go_live_checklist": go_live_checklist_report(),
            "known_limitations": known_limitations_doc(),
            "roadmap_v2": roadmap_v2_doc(),
        },
        "legacy_routes": [
            "/pilot-checklist",
            "/security-compliance",
            "/monitoring",
            "/production-deployment/checklist",
        ],
    }


def dashboard_payload() -> dict[str, Any]:
    ensure_readiness_pack()
    dash = readiness_pack_dashboard()
    inventory = readiness_pack_inventory()
    return {
        "platform": "Readiness Pack",
        "phase": "5.14",
        "sprint": "Readiness Pack",
        "status": dash["status"],
        "read_only": True,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "system_score": dash["system_score"],
            "security_score": dash["security_score"],
            "pilot_score": dash["pilot_score"],
            "checklist_remaining": dash["checklist_remaining"],
            "artifacts_present": dash["artifacts_present"],
            "artifacts_total": inventory["artifacts_total"],
            "missing_count": len(inventory["missing"]),
        },
        "features": list(FEATURES),
        "inventory": inventory["items"],
    }


def write_generated_artifacts() -> dict[str, Any]:
    """Persist live system and checklist snapshots for verify/report consumers."""
    GENERATED.mkdir(parents=True, exist_ok=True)
    system = system_readiness_report()
    checklist = go_live_checklist_report()
    READINESS_ASSETS["system_report"].write_text(json.dumps(system, indent=2, default=str), encoding="utf-8")
    checklist_payload = {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "5.14",
        "sprint": "Readiness Pack",
        "summary": {
            "items_total": checklist["items_total"],
            "items_checked": checklist["items_checked"],
            "items_remaining": checklist["items_remaining"],
            "ok": checklist["items_remaining"] == 0,
        },
        "items": checklist["items"],
        "verify_scripts": checklist.get("verify_scripts", []),
    }
    READINESS_ASSETS["go_live_checklist"].write_text(
        json.dumps(checklist_payload, indent=2, default=str),
        encoding="utf-8",
    )
    return {
        "system_report": str(READINESS_ASSETS["system_report"]),
        "go_live_checklist": str(READINESS_ASSETS["go_live_checklist"]),
    }
