"""Operations runbooks business logic for Phase 5 Sprint 5.11."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

OPERATIONS_RUNBOOKS_ROLES = ("SUPER_ADMIN", "ADMIN")

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent

RUNBOOK_FILES = {
    "go_live": {
        "title": "Go-Live Runbook",
        "filename": "GO_LIVE_RUNBOOK.md",
        "path": REPO / "docs" / "GO_LIVE_RUNBOOK.md",
        "summary": "Pre-cutover checklist, cutover steps, and post go-live validation.",
    },
    "backup": {
        "title": "Backup Runbook",
        "filename": "BACKUP_RUNBOOK.md",
        "path": REPO / "docs" / "BACKUP_RUNBOOK.md",
        "summary": "Scheduled and manual backup procedures with retention policy.",
    },
    "restore": {
        "title": "Restore Runbook",
        "filename": "RESTORE_RUNBOOK.md",
        "path": REPO / "docs" / "RESTORE_RUNBOOK.md",
        "summary": "Dry-run, maintenance, restore, and validation workflow.",
    },
    "rollback": {
        "title": "Rollback Runbook",
        "filename": "ROLLBACK_RUNBOOK.md",
        "path": REPO / "docs" / "ROLLBACK_RUNBOOK.md",
        "summary": "Application and database rollback with validation artifacts.",
    },
    "incident": {
        "title": "Incident Runbook",
        "filename": "INCIDENT_RUNBOOK.md",
        "path": REPO / "docs" / "INCIDENT_RUNBOOK.md",
        "summary": "Severity levels, triage, diagnostics, and escalation.",
    },
}

FEATURES = tuple(item["filename"] for item in RUNBOOK_FILES.values())


def ensure_operations_runbooks() -> dict[str, Any]:
    return {"ready": True, "read_only": True}


def _read_runbook(key: str) -> dict[str, Any]:
    ensure_operations_runbooks()
    meta = RUNBOOK_FILES[key]
    path: Path = meta["path"]
    content = ""
    if path.exists():
        content = path.read_text(encoding="utf-8")
    try:
        path_display = str(path.relative_to(REPO))
    except ValueError:
        path_display = str(path)
    sections = [line.lstrip("#").strip() for line in content.splitlines() if line.startswith("## ")]
    return {
        "report": f"{key}_runbook",
        "read_only": True,
        "key": key,
        "title": meta["title"],
        "filename": meta["filename"],
        "path": path_display,
        "exists": path.exists(),
        "summary": meta["summary"],
        "sections": sections,
        "content": content,
        "size_bytes": len(content.encode("utf-8")),
    }


def go_live_runbook() -> dict[str, Any]:
    return _read_runbook("go_live")


def backup_runbook() -> dict[str, Any]:
    return _read_runbook("backup")


def restore_runbook() -> dict[str, Any]:
    return _read_runbook("restore")


def rollback_runbook() -> dict[str, Any]:
    return _read_runbook("rollback")


def incident_runbook() -> dict[str, Any]:
    return _read_runbook("incident")


def operations_runbooks_inventory() -> dict[str, Any]:
    ensure_operations_runbooks()
    items = []
    for key in RUNBOOK_FILES:
        payload = _read_runbook(key)
        items.append(
            {
                "key": key,
                "title": payload["title"],
                "filename": payload["filename"],
                "exists": payload["exists"],
                "sections_count": len(payload["sections"]),
                "size_bytes": payload["size_bytes"],
            }
        )
    missing = [item["filename"] for item in items if not item["exists"]]
    return {
        "report": "operations_runbooks_inventory",
        "read_only": True,
        "runbooks_total": len(items),
        "runbooks_present": len(items) - len(missing),
        "missing": missing,
        "items": items,
    }


def operations_runbooks_dashboard() -> dict[str, Any]:
    inventory = operations_runbooks_inventory()
    status = "OK" if not inventory["missing"] else "WARN"
    return {
        "report": "operations_runbooks_dashboard",
        "read_only": True,
        "status": status,
        "runbooks_total": inventory["runbooks_total"],
        "runbooks_present": inventory["runbooks_present"],
        "missing": inventory["missing"],
    }


def operations_runbooks_readiness_report() -> dict[str, Any]:
    dashboard = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "5.11",
        "sprint": "Operations Runbooks",
        "platform": dashboard["platform"],
        "status": dashboard["status"],
        "summary": dashboard["summary"],
        "features": list(FEATURES),
        "sections": {
            "go_live": go_live_runbook(),
            "backup": backup_runbook(),
            "restore": restore_runbook(),
            "rollback": rollback_runbook(),
            "incident": incident_runbook(),
        },
        "legacy_routes": [
            "/backup-recovery/runbook",
            "/release-management/rollback",
            "/monitoring",
            "docs/RUNBOOK.md",
        ],
    }


def dashboard_payload() -> dict[str, Any]:
    ensure_operations_runbooks()
    dash = operations_runbooks_dashboard()
    inventory = operations_runbooks_inventory()
    return {
        "platform": "Operations Runbooks",
        "phase": "5.11",
        "sprint": "Operations Runbooks",
        "status": dash["status"],
        "read_only": True,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "runbooks_total": dash["runbooks_total"],
            "runbooks_present": dash["runbooks_present"],
            "missing_count": len(dash["missing"]),
        },
        "features": list(FEATURES),
        "inventory": inventory["items"],
    }
