"""Release 2.0 Architecture Freeze — shared inventory and guardrail helpers."""

from __future__ import annotations

import ast
import importlib
import inspect
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
GENERATED = ROOT / "generated_release"
DOCS_ARCH = REPO / "docs" / "architecture"
BASELINE_PATH = GENERATED / "RELEASE_2_BASELINE_SNAPSHOT.json"

EXPERIMENTAL_MARKERS = ("sandbox", "foundation", "beta", "future", "experimental", "plugin")
DEPRECATED_MARKERS = ("deprecated", "/api/v2/")
INTERNAL_WEB_PREFIXES = ("/app/", "/marketplace", "/doctor", "/lab/", "/admin/")
STABLE_API_PREFIX = "/api/v1/"

FROZEN_EVENT_ENVELOPE_FIELDS = (
    "event_id",
    "event_type",
    "event_version",
    "occurred_at",
    "organization_id",
    "actor_id",
    "correlation_id",
    "causation_id",
    "resource_type",
    "resource_id",
    "payload",
    "metadata",
)

FROZEN_CORE_EVENTS = [
    "patient.created",
    "order.created",
    "order.confirmed",
    "payment.confirmed",
    "collection.assigned",
    "sample.collected",
    "sample.in_transit",
    "sample.received",
    "sample.rejected",
    "result.entered",
    "result.validated",
    "report.approved",
    "report.released",
    "appointment.created",
    "consultation.requested",
    "prescription.created",
    "incident.created",
]

FROZEN_ORDER_STATES = [
    "CREATED", "CONFIRMED", "PAYMENT_PENDING", "PAID", "COLLECTION_SCHEDULED",
    "COLLECTOR_ASSIGNED", "COLLECTION_IN_PROGRESS", "COLLECTED", "IN_TRANSIT",
    "LAB_RECEIVED", "TESTING", "QC_PENDING", "VALIDATION_PENDING", "REPORT_PENDING",
    "RELEASED", "CLOSED", "CANCELLED",
]

FROZEN_SAMPLE_STATES = [
    "CREATED", "LABELLED", "COLLECTED", "PACKED", "IN_TRANSIT", "RECEIVED",
    "ACCEPTED", "REJECTED", "TESTING", "COMPLETED", "DISPOSED",
]

FROZEN_RESULT_STATES = [
    "DRAFT", "ENTERED", "QC_PENDING", "QC_PASSED", "VALIDATION_REQUIRED",
    "PENDING_REVIEW", "APPROVED", "RELEASED", "AMENDED", "REJECTED",
]

TENANT_EXEMPT_TABLES = {
    "alembic_version",
    "users",
    "organizations",
    "organization_memberships",
    "roles",
    "permissions",
    "feature_flags",
    "system_settings",
    "audit_logs",
    "intg_audit_events",
}

DESTRUCTIVE_SQL_PATTERNS = [
    re.compile(r"\bDROP\s+TABLE\b", re.I),
    re.compile(r"\bDROP\s+COLUMN\b", re.I),
    re.compile(r"\bTRUNCATE\b", re.I),
    re.compile(r"\bDELETE\s+FROM\b", re.I),
]

SECRET_PATTERNS = [
    re.compile(r'password\s*=\s*["\'][^"\']+["\']', re.I),
    re.compile(r'api[_-]?key\s*=\s*["\'][^"\']+["\']', re.I),
    re.compile(r'secret\s*=\s*["\'][^"\']{8,}["\']', re.I),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_report(name: str, payload: dict[str, Any]) -> Path:
    GENERATED.mkdir(parents=True, exist_ok=True)
    path = GENERATED / name
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def create_app():
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app as _create

    return _create()


def classify_route(path: str, endpoint: str) -> str:
    lower = path.lower()
    if any(m in lower for m in DEPRECATED_MARKERS):
        return "DEPRECATED"
    if any(m in lower for m in EXPERIMENTAL_MARKERS):
        return "EXPERIMENTAL"
    if path.startswith(STABLE_API_PREFIX):
        if any(m in lower for m in ("internal", "_debug", "metrics")):
            return "INTERNAL"
        return "STABLE"
    if path.startswith(INTERNAL_WEB_PREFIXES) or not path.startswith("/api/"):
        return "INTERNAL"
    return "INTERNAL"


def inventory_api_routes(app) -> dict[str, Any]:
    from app.api_platform.api_inventory import scan_routes

    scanned = scan_routes(app)
    all_rules = []
    classification: dict[str, list[dict]] = {
        "STABLE": [],
        "EXPERIMENTAL": [],
        "DEPRECATED": [],
        "INTERNAL": [],
    }
    for rule in app.url_map.iter_rules():
        path = str(rule)
        methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
        entry = {
            "path": path,
            "methods": methods,
            "endpoint": rule.endpoint,
            "classification": classify_route(path, rule.endpoint),
        }
        all_rules.append(entry)
        classification[entry["classification"]].append(entry)

    api_v1 = [r for r in all_rules if r["path"].startswith("/api/v1/")]
    return {
        "generated_at": utc_now(),
        "total_routes": len(all_rules),
        "api_v1_routes": len(api_v1),
        "stable_count": len(classification["STABLE"]),
        "experimental_count": len(classification["EXPERIMENTAL"]),
        "deprecated_count": len(classification["DEPRECATED"]),
        "internal_count": len(classification["INTERNAL"]),
        "classification": {k: len(v) for k, v in classification.items()},
        "duplicates": scanned.get("duplicates", []),
        "duplicate_count": len(scanned.get("duplicates", [])),
        "sample_stable": [r["path"] for r in classification["STABLE"][:30]],
        "sample_experimental": [r["path"] for r in classification["EXPERIMENTAL"][:15]],
    }


def inventory_database() -> dict[str, Any]:
    from app.extensions.db import db

    tables: list[dict[str, Any]] = []
    tenant_missing: list[str] = []
    for name, table in sorted(db.metadata.tables.items()):
        cols = {c.name: str(c.type) for c in table.columns}
        tenant_cols = [c for c in ("organization_id", "tenant_id", "org_id") if c in cols]
        fks = [f"{fk.parent.name}->{fk.target_fullname}" for fk in table.foreign_keys]
        uniques = [list(u.columns.keys()) for u in table.constraints if u.__class__.__name__ == "UniqueConstraint"]
        indexes = [idx.name for idx in table.indexes]
        entry = {
            "table": name,
            "columns": len(cols),
            "tenant_columns": tenant_cols,
            "foreign_keys": fks[:10],
            "unique_constraints": uniques[:5],
            "indexes": indexes[:10],
        }
        tables.append(entry)
        if name not in TENANT_EXEMPT_TABLES and not tenant_cols:
            if not name.startswith(("intg_", "system_", "feature_")):
                tenant_missing.append(name)

    migrations = sorted((ROOT / "migrations").glob("*.sql"))
    destructive: list[dict] = []
    for mig in migrations:
        text = mig.read_text(encoding="utf-8")
        for pattern in DESTRUCTIVE_SQL_PATTERNS:
            if pattern.search(text):
                destructive.append({"file": mig.name, "pattern": pattern.pattern})

    return {
        "generated_at": utc_now(),
        "table_count": len(tables),
        "migration_count": len(migrations),
        "migrations": [m.name for m in migrations],
        "tenant_missing_count": len(tenant_missing),
        "tenant_missing_sample": tenant_missing[:25],
        "destructive_migration_hits": destructive,
        "tables_sample": tables[:40],
    }


def inventory_permissions() -> dict[str, Any]:
    from app.core.permissions import ROLE_PERMISSIONS
    from app.integration.constants import INTEGRATION_PERMISSIONS

    perms: set[str] = set()
    for role, values in ROLE_PERMISSIONS.items():
        perms.update(values)
    perms.discard("*")
    perms.update(INTEGRATION_PERMISSIONS)

    marketplace_perms = {
        "MARKETPLACE_VIEW",
        "MARKETPLACE_LISTING_MANAGE",
        "MARKETPLACE_LISTING_APPROVE",
        "MARKETPLACE_PRICE_MANAGE",
        "PROMOTION_MANAGE",
        "PAYMENT_VIEW",
        "PAYMENT_RECONCILE",
    }
    return {
        "generated_at": utc_now(),
        "role_count": len(ROLE_PERMISSIONS),
        "registered_permission_count": len(perms),
        "integration_permissions": list(INTEGRATION_PERMISSIONS),
        "marketplace_permissions_declared": sorted(marketplace_perms),
        "sample_permissions": sorted(perms)[:40],
    }


def inventory_domain_events() -> dict[str, Any]:
    from app.core.statuses import VALID_DOMAIN_EVENTS
    from app.events.domain_event import DomainEvent

    legacy_map = {
        "PatientCreated": "patient.created",
        "BookingCreated": "appointment.created",
        "OrderCreated": "order.created",
        "CollectorAssigned": "collection.assigned",
        "SampleCollected": "sample.collected",
        "SampleReceived": "sample.received",
        "ResultApproved": "result.validated",
        "ResultReleased": "report.released",
        "InvoicePaid": "payment.confirmed",
        "InvoiceCreated": "payment.confirmed",
    }
    implemented = set(VALID_DOMAIN_EVENTS)
    envelope_in_code = set(DomainEvent.__dataclass_fields__)
    return {
        "generated_at": utc_now(),
        "frozen_event_count": len(FROZEN_CORE_EVENTS),
        "implemented_legacy_events": sorted(implemented),
        "legacy_to_dot_notation": legacy_map,
        "envelope_fields_required": list(FROZEN_EVENT_ENVELOPE_FIELDS),
        "envelope_fields_in_dataclass": sorted(envelope_in_code),
        "envelope_gap": [f for f in FROZEN_EVENT_ENVELOPE_FIELDS if f not in envelope_in_code],
    }


def inventory_state_machines() -> dict[str, Any]:
    from app.core import statuses as st

    machines = {}
    for name in ("MEDICAL_ORDER_TRANSITIONS", "LAB_RESULT_TRANSITIONS"):
        transitions = getattr(st, name, None)
        if isinstance(transitions, dict):
            machines[name] = {
                "state_count": len(transitions),
                "terminal_checks": True,
            }
    sample_statuses = getattr(st, "VALID_SAMPLE_STATUSES", [])
    result_statuses = getattr(st, "VALID_LAB_RESULT_STATUSES", [])
    return {
        "generated_at": utc_now(),
        "frozen_order_states": FROZEN_ORDER_STATES,
        "frozen_sample_states": FROZEN_SAMPLE_STATES,
        "frozen_result_states": FROZEN_RESULT_STATES,
        "implemented_medical_order_states": getattr(st, "VALID_MEDICAL_ORDER_STATUSES", []),
        "implemented_sample_states": sample_statuses,
        "implemented_result_states": result_statuses,
        "transition_maps": machines,
        "order_state_coverage": len(set(getattr(st, "VALID_MEDICAL_ORDER_STATUSES", [])) & set(FROZEN_ORDER_STATES)),
    }


def inventory_integration_contract() -> dict[str, Any]:
    from app.integration.adapters import ADAPTER_REGISTRY
    from app.integration.constants import CONNECTOR_TYPES, PROTOCOLS, WEBHOOK_EVENTS

    return {
        "generated_at": utc_now(),
        "connector_types": CONNECTOR_TYPES,
        "protocols": PROTOCOLS,
        "webhook_events": WEBHOOK_EVENTS,
        "adapters": {
            name: {"production_ready": cls.production_ready}
            for name, cls in ADAPTER_REGISTRY.items()
        },
    }


def inventory_canonical_models() -> dict[str, Any]:
    from app.integration.mappings.canonical import (
        CANONICAL_ORDER_FIELDS,
        CANONICAL_PATIENT_FIELDS,
        CANONICAL_REPORT_FIELDS,
        CANONICAL_RESULT_FIELDS,
        CANONICAL_SAMPLE_FIELDS,
    )

    return {
        "generated_at": utc_now(),
        "schema_version": "1.0",
        "entities": {
            "Patient": list(CANONICAL_PATIENT_FIELDS),
            "Order": list(CANONICAL_ORDER_FIELDS),
            "Sample": list(CANONICAL_SAMPLE_FIELDS),
            "Result": list(CANONICAL_RESULT_FIELDS),
            "Report": list(CANONICAL_REPORT_FIELDS),
        },
    }


def check_guardrails(app) -> dict[str, Any]:
    findings: list[dict] = []
    critical: list[str] = []
    warnings: list[str] = []

    api = inventory_api_routes(app)
    if api["duplicate_count"] > 0:
        critical.append("duplicate_api_routes")

    db_info = inventory_database()
    if db_info["destructive_migration_hits"]:
        critical.append("destructive_migrations_detected")

    perm_info = inventory_permissions()
    if perm_info["registered_permission_count"] < 10:
        warnings.append("low_permission_registry_count")

    event_info = inventory_domain_events()
    if event_info["envelope_gap"]:
        warnings.append("domain_event_envelope_not_fully_aligned")

    state_info = inventory_state_machines()
    if not state_info["transition_maps"]:
        critical.append("missing_clinical_transition_maps")

    secret_hits = scan_secret_patterns()
    if secret_hits:
        critical.append("potential_secrets_in_config")

    demo_mode = scan_demo_mode_flags()
    if demo_mode:
        warnings.append("demo_mode_references_found")

    for item in critical:
        findings.append({"severity": "CRITICAL", "code": item})
    for item in warnings:
        findings.append({"severity": "WARNING", "code": item})

    return {
        "generated_at": utc_now(),
        "critical_count": len(critical),
        "warning_count": len(warnings),
        "critical": critical,
        "warnings": warnings,
        "findings": findings,
        "ok": len(critical) == 0,
    }


def scan_secret_patterns() -> list[dict]:
    hits = []
    for path in (REPO / "backend" / ".env.example", REPO / "backend" / ".env.staging.example"):
        if not path.exists():
            continue
        for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip().startswith("#"):
                continue
            for pattern in SECRET_PATTERNS:
                if pattern.search(line) and "changeme" not in line.lower() and "example" not in line.lower():
                    hits.append({"file": str(path.relative_to(REPO)), "line": idx})
    return hits


def scan_demo_mode_flags() -> list[str]:
    hits = []
    web_env = REPO / "apps" / "web" / ".env.example"
    if web_env.exists() and "DEMO_MODE=true" in web_env.read_text(encoding="utf-8"):
        hits.append(str(web_env))
    return hits


def save_baseline_snapshot(app) -> None:
    snapshot = {
        "generated_at": utc_now(),
        "api": inventory_api_routes(app),
        "stable_route_paths": sorted(
            str(r)
            for r in app.url_map.iter_rules()
            if classify_route(str(r), r.endpoint) == "STABLE"
        ),
    }
    write_report("RELEASE_2_BASELINE_SNAPSHOT.json", snapshot)
    BASELINE_PATH.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")


def check_stable_routes_preserved(app) -> dict[str, Any]:
    if not BASELINE_PATH.exists():
        return {"ok": True, "skipped": True, "reason": "no baseline yet"}
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    current_stable = {
        str(r)
        for r in app.url_map.iter_rules()
        if classify_route(str(r), r.endpoint) == "STABLE"
    }
    baseline_stable = set(baseline.get("stable_route_paths", []))
    removed = sorted(baseline_stable - current_stable)
    return {
        "ok": len(removed) == 0,
        "removed_count": len(removed),
        "removed_sample": removed[:20],
    }


def build_baseline_certificate(sections: dict[str, Any]) -> dict[str, Any]:
    critical = sum(
        1
        for section in sections.values()
        if isinstance(section, dict) and section.get("critical_count", 0) > 0
    )
    guardrails = sections.get("guardrails", {})
    script_keys = [k for k in sections if k.startswith("verify_") and k.endswith(".py")]
    scripts_ok = all(sections[k].get("ok") for k in script_keys if isinstance(sections.get(k), dict))
    guardrails_ok = guardrails.get("ok", guardrails.get("critical_count", 1) == 0)
    warnings = guardrails.get("warning_count", 0)
    if critical > 0 or not scripts_ok or not guardrails_ok:
        result = "FAIL"
    elif warnings > 0:
        result = "PASS_WITH_WARNINGS"
    else:
        result = "PASS"
    return {
        "generated_at": utc_now(),
        "release": "2.0",
        "result": result,
        "critical_findings": critical,
        "warning_count": warnings,
        "sections": {
            k: (v.get("ok") if isinstance(v, dict) else None)
            for k, v in sections.items()
            if k.startswith("verify_")
        },
    }


def run_unit_tests() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    total = None
    for line in proc.stdout.splitlines():
        if line.startswith("Ran "):
            try:
                total = int(line.split()[1])
            except (IndexError, ValueError):
                pass
    return {"ok": proc.returncode == 0, "total": total, "exit_code": proc.returncode}
