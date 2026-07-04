#!/usr/bin/env python3
"""Verify Healthcare Standards Advanced Phase 4 Sprint 4.4."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "STANDARDS_ADVANCED_REPORT.json"

WEB_ROUTES = (
    "/standards-advanced",
    "/standards-advanced/hl7-oru",
    "/standards-advanced/hl7-orm",
    "/standards-advanced/hl7-adt",
    "/standards-advanced/fhir-patient",
    "/standards-advanced/fhir-diagnostic",
    "/standards-advanced/fhir-observation",
    "/standards-advanced/loinc",
    "/standards-advanced/icd10",
    "/standards-advanced/audit",
    "/standards-advanced/sandbox",
)

API_ROUTES = (
    "/api/v1/standards-advanced/dashboard",
    "/api/v1/standards-advanced/audit",
    "/api/v1/standards-advanced/sandbox/messages",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _login_admin(client):
    from app.models.user import User

    user = User.query.filter(User.role == "SUPER_ADMIN").first()
    if not user:
        user = User.query.filter(User.role == "ADMIN").first()
    if not user:
        return False
    with client.session_transaction() as sess:
        sess["user_id"] = user.id
        sess["role"] = user.role
        sess["email"] = user.email
    return True


def _api_json(response):
    payload = response.get_json() or {}
    if isinstance(payload, dict) and payload.get("success") is True and "data" in payload:
        return payload["data"]
    return payload


def main() -> int:
    sys.path.insert(0, str(ROOT))
    if not os.getenv("DATABASE_URL"):
        print("FAIL: DATABASE_URL is required", file=sys.stderr)
        return 1

    print("\n=== DXCON HEALTHCARE STANDARDS ADVANCED VERIFY ===\n")
    start = time.perf_counter()
    checks: dict[str, dict] = {}

    from app import create_app

    app = create_app()
    with app.app_context():
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User

        db.create_all()
        if not User.query.filter(User.role.in_(("SUPER_ADMIN", "ADMIN"))).first():
            db.session.add(
                User(
                    email="verify-standards@demo.dxcon.test",
                    role="ADMIN",
                    password_hash=hash_password("DemoPass123!"),
                    is_active=True,
                )
            )
            db.session.commit()

        from scripts.seed_standards_demo import seed_all

        seed_all()

        routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
        missing_web = [route for route in WEB_ROUTES if route not in routes]
        missing_api = [route for route in API_ROUTES if route not in routes]
        checks["route_registry"] = {
            "ok": not missing_web and not missing_api,
            "missing_web": missing_web,
            "missing_api": missing_api,
        }

        client = app.test_client()
        if not _login_admin(client):
            checks["auth"] = {"ok": False, "reason": "no admin user"}
        else:
            checks["auth"] = {"ok": True}

        web_ok = True
        web_results = {}
        for route in WEB_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200 and len(response.get_data(as_text=True)) > 200
            web_ok = web_ok and ok
            web_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["standards_advanced_dashboard"] = {"ok": web_ok, "routes": web_results}

        api_ok = True
        api_results = {}
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        from app.services.standards_advanced_service import FEATURES, dashboard_payload, sandbox_messages

        dashboard = dashboard_payload()
        sandbox = sandbox_messages()

        oru = _api_json(
            client.post(
                "/api/v1/standards-advanced/hl7/oru/export",
                json={"patient_id": "PAT-001", "order_id": "ORD-001", "value": "95"},
            )
        )
        checks["hl7_oru_result_export"] = {
            "ok": oru.get("message_type") == "ORU" and bool(oru.get("export")),
        }

        orm = _api_json(
            client.post(
                "/api/v1/standards-advanced/hl7/orm/import",
                json={"message": sandbox["hl7"]["orm"]},
            )
        )
        checks["hl7_orm_order_import"] = {
            "ok": orm.get("message_type") == "ORM" and "normalized" in orm,
        }

        adt = _api_json(
            client.post(
                "/api/v1/standards-advanced/hl7/adt/import",
                json={"message": sandbox["hl7"]["adt"]},
            )
        )
        checks["hl7_adt_patient_import"] = {
            "ok": adt.get("message_type") == "ADT" and "normalized" in adt,
        }

        patient = _api_json(
            client.post(
                "/api/v1/standards-advanced/fhir/patient/map",
                json={"patient_id": "PAT-001", "name": "Demo^Patient", "gender": "M"},
            )
        )
        checks["fhir_patient_mapping"] = {
            "ok": patient.get("resource", {}).get("resourceType") == "Patient",
        }

        diagnostic = _api_json(
            client.post(
                "/api/v1/standards-advanced/fhir/diagnostic-report/map",
                json={
                    "patient_id": "PAT-001",
                    "order_id": "ORD-001",
                    "value": "95",
                    "service_code": "SVC-001",
                },
            )
        )
        checks["fhir_diagnostic_report_mapping"] = {
            "ok": diagnostic.get("diagnostic_report", {}).get("resourceType") == "DiagnosticReport",
        }

        observation = _api_json(
            client.post(
                "/api/v1/standards-advanced/fhir/observation/map",
                json={
                    "patient_id": "PAT-001",
                    "order_id": "ORD-001",
                    "value": "95",
                    "service_code": "SVC-001",
                },
            )
        )
        checks["fhir_observation_mapping"] = {
            "ok": observation.get("observation", {}).get("resourceType") == "Observation",
        }

        loinc = _api_json(client.post("/api/v1/standards-advanced/loinc/validate", json={"code": "LNC-0001"}))
        checks["loinc_mapping_validation"] = {"ok": loinc.get("valid") is True}

        icd = _api_json(client.post("/api/v1/standards-advanced/icd10/validate", json={"code": "I10-0001"}))
        checks["icd10_mapping_validation"] = {"ok": icd.get("valid") is True}

        audit = _api_json(client.get("/api/v1/standards-advanced/audit"))
        checks["standards_audit_log"] = {"ok": audit.get("count", 0) >= 1}

        sandbox_api = _api_json(client.get("/api/v1/standards-advanced/sandbox/messages"))
        checks["integration_sandbox_messages"] = {
            "ok": sandbox_api.get("sandbox") is True and "hl7" in sandbox_api and "fhir" in sandbox_api,
        }

        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 11 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

        existing = client.get("/api/v1/standards/code-systems")
        checks["existing_standards_api_preserved"] = {
            "ok": existing.status_code == 200 and _api_json(existing).get("count", 0) >= 1,
        }

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "4.4",
        "sprint": "Healthcare Standards Advanced",
        "summary": {
            "score": score,
            "checks_passed": passed,
            "checks_total": total,
            "ok": passed == total,
            "runtime_seconds": round(time.perf_counter() - start, 3),
        },
        "checks": checks,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(f"Healthcare Standards Advanced score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("HEALTHCARE STANDARDS ADVANCED VERIFY PASS\n")
        return 0
    print("HEALTHCARE STANDARDS ADVANCED VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
