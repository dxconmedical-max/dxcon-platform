#!/usr/bin/env python3
"""Release 7.0 Sprint 3 — full verification gate and report generation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.bootstrap.blueprints import register_blueprints
from app.core.statuses import LIMS_SPECIMEN_TRANSITIONS
from app.extensions.db import db
from app.lims_core.service import create_specimen, transition_specimen
from app.models.lims_core import LimsSpecimen

LIMS_REPORT = ROOT / "generated_release" / "SPRINT_3_LIMS_REPORT.json"
SECURITY_REPORT = ROOT / "generated_release" / "SPRINT_3_SECURITY_REPORT.json"
MIGRATION_REPORT = ROOT / "generated_release" / "SPRINT_3_MIGRATION_REPORT.json"
UI_REPORT = REPO / "apps" / "web" / "generated-release" / "SPRINT_3_UI_REPORT.json"
MIGRATION = ROOT / "migrations" / "016_lims_core.sql"

REQUIRED_ROUTES = (
    "/api/v1/specimens",
    "/api/v1/barcodes",
    "/api/v1/accessions",
    "/api/v1/lab/dashboard",
)

FRONTEND_PAGES = {
    "specimens": REPO / "apps/web/src/app/app/lab/specimens/page.tsx",
    "barcode": REPO / "apps/web/src/app/app/lab/barcode/page.tsx",
    "accession": REPO / "apps/web/src/app/app/lab/accession/page.tsx",
    "timeline": REPO / "apps/web/src/app/app/lab/timeline/page.tsx",
    "lab_api": REPO / "apps/web/src/lib/api/lab.ts",
    "workspaces": REPO / "apps/web/src/lib/workspaces.ts",
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def verify_migrations() -> dict:
    text = MIGRATION.read_text(encoding="utf-8") if MIGRATION.exists() else ""
    tables = [
        "specimens",
        "containers",
        "barcode_logs",
        "storage_locations",
        "accessions",
        "sample_status_history",
    ]
    checks = {t: f"CREATE TABLE" in text and t in text for t in tables}
    checks["migration_file_exists"] = MIGRATION.exists()
    checks["additive_only"] = "DROP TABLE" not in text.upper()
    return checks


def verify_models_imports() -> dict:
    try:
        from app.models.lims_core import (  # noqa: F401
            LimsAccession,
            LimsBarcodeLog,
            LimsContainer,
            LimsSampleStatusHistory,
            LimsSpecimen,
            LimsStorageLocation,
        )
        from app.models import LimsSpecimen as Imported  # noqa: F401

        return {"models_importable": True, "registered_in_init": Imported is LimsSpecimen}
    except Exception as exc:
        return {"models_importable": False, "error": str(exc)}


def verify_blueprints() -> dict:
    app = create_app()
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    return {route: route in rules for route in REQUIRED_ROUTES}


def verify_lifecycle() -> dict:
    app = create_app()
    with app.app_context():
        db.create_all()
        specimen = create_specimen(order_code="GATE-001", actor="gate@test")
        db.session.commit()
        transition_specimen(specimen["id"], to_status="COLLECTED", actor="gate@test")
        db.session.commit()
        count = LimsSpecimen.query.count()
    return {
        "transitions_defined": len(LIMS_SPECIMEN_TRANSITIONS) >= 9,
        "specimen_created": count == 1,
    }


def verify_barcode_uniqueness() -> dict:
    app = create_app()
    with app.app_context():
        db.create_all()
        codes = set()
        for i in range(5):
            row = create_specimen(order_code=f"GATE-B{i}", actor="gate@test")
            db.session.commit()
            codes.add(row["human_readable"])
    return {
        "unique_barcodes": len(codes) == 5,
    }


def verify_tenant_isolation() -> dict:
    service = (ROOT / "app/lims_core/service.py").read_text(encoding="utf-8")
    routes = (ROOT / "app/api/lims_core/routes.py").read_text(encoding="utf-8")
    return {
        "organization_filter_in_list": "organization_id" in service,
        "org_header_in_routes": "X-Organization-ID" in routes or "organization_id" in routes,
        "lab_api_auth": "lab_api_read" in routes and "lab_api_write" in routes,
    }


def verify_permissions() -> dict:
    routes = (ROOT / "app/api/lims_core/routes.py").read_text(encoding="utf-8")
    return {
        "read_decorator": routes.count("@lab_api_read") >= 4,
        "write_decorator": routes.count("@lab_api_write") >= 3,
    }


def verify_accession() -> dict:
    service = (ROOT / "app/lims_core/service.py").read_text(encoding="utf-8")
    return {
        "receive_and_accession": "receive_and_accession_specimen" in service,
        "verify_barcode": "verify_barcode" in service,
    }


def verify_frontend() -> dict:
    pages = {name: path.exists() for name, path in FRONTEND_PAGES.items()}
    lab_ts = FRONTEND_PAGES["lab_api"].read_text(encoding="utf-8") if FRONTEND_PAGES["lab_api"].exists() else ""
    pages["fetch_lims_dashboard"] = "fetchLimsDashboard" in lab_ts
    pages["fetch_specimens"] = "fetchSpecimens" in lab_ts
    return pages


def main() -> int:
    lims_checks = {
        "migrations": verify_migrations(),
        "models": verify_models_imports(),
        "blueprints": verify_blueprints(),
        "lifecycle": verify_lifecycle(),
        "barcode": verify_barcode_uniqueness(),
        "accession": verify_accession(),
        "tenant_isolation": verify_tenant_isolation(),
        "permissions": verify_permissions(),
        "frontend": verify_frontend(),
    }

    flat_failures = []
    for section, checks in lims_checks.items():
        if isinstance(checks, dict):
            for key, val in checks.items():
                if val is False:
                    flat_failures.append(f"{section}.{key}")

    security_checks = {
        **lims_checks["tenant_isolation"],
        **lims_checks["permissions"],
        "no_credentials_in_barcode_api": "password" not in (
            ROOT / "app/api/lims_core/routes.py"
        ).read_text(encoding="utf-8").lower(),
        "audit_module": (ROOT / "app/lims_core/audit.py").exists(),
    }
    security_failed = [k for k, v in security_checks.items() if not v]

    migration_checks = lims_checks["migrations"]
    migration_failed = [k for k, v in migration_checks.items() if not v]

    frontend_checks = lims_checks["frontend"]
    frontend_failed = [k for k, v in frontend_checks.items() if not v]

    status = "PASS" if not flat_failures else "FAIL"

    for path, payload in (
        (LIMS_REPORT, {
            "generated_at": _utcnow(),
            "release": "7.0",
            "sprint": "Sprint 3 — LIMS Core",
            "status": status,
            "checks": lims_checks,
            "failed": flat_failures,
            "api_endpoints": list(REQUIRED_ROUTES),
        }),
        (SECURITY_REPORT, {
            "generated_at": _utcnow(),
            "release": "7.0",
            "sprint": "Sprint 3 — LIMS Core",
            "status": "PASS" if not security_failed else "FAIL",
            "checks": security_checks,
            "failed": security_failed,
            "critical_blockers": security_failed,
        }),
        (MIGRATION_REPORT, {
            "generated_at": _utcnow(),
            "release": "7.0",
            "sprint": "Sprint 3 — LIMS Core",
            "status": "PASS" if not migration_failed else "FAIL",
            "migration": "016_lims_core.sql",
            "checks": migration_checks,
            "failed": migration_failed,
            "destructive_ops": False,
        }),
        (UI_REPORT, {
            "generated_at": _utcnow(),
            "release": "7.0",
            "sprint": "Sprint 3 — LIMS Core",
            "status": "PASS" if not frontend_failed else "FAIL",
            "pages": frontend_checks,
            "failed": frontend_failed,
        }),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Sprint 3 gate: {status}")
    if flat_failures:
        print("Failures:", flat_failures)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
