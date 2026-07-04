#!/usr/bin/env python3
"""Verify AI Clinical Platform Phase 4 Sprint 4.2 routes, API, and advisory policy."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "AI_CLINICAL_REPORT.json"

WEB_ROUTES = (
    "/ai-clinical",
    "/ai-clinical/providers",
    "/ai-clinical/prompts",
    "/ai-clinical/router",
    "/ai-clinical/interpret",
    "/ai-clinical/critical",
    "/ai-clinical/delta",
    "/ai-clinical/reference-ranges",
    "/ai-clinical/summary",
    "/ai-clinical/patient-friendly",
    "/ai-clinical/review-flags",
    "/ai-clinical/audit",
    "/ai-clinical/usage",
    "/ai-clinical/safety",
)

API_ROUTES = (
    "/api/v1/ai-clinical/dashboard",
    "/api/v1/ai-clinical/providers",
    "/api/v1/ai-clinical/prompts",
    "/api/v1/ai-clinical/router",
    "/api/v1/ai-clinical/doctor-review-flag",
    "/api/v1/ai-clinical/audit",
    "/api/v1/ai-clinical/usage",
    "/api/v1/ai-clinical/safety/disclaimer",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _login_clinical(client):
    from app.models.user import User

    user = User.query.filter(User.role == "DOCTOR").first()
    if not user:
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

    print("\n=== DXCON AI CLINICAL PLATFORM VERIFY ===\n")
    start = time.perf_counter()
    checks: dict[str, dict] = {}

    from app import create_app

    app = create_app()
    with app.app_context():
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User

        db.create_all()
        if not User.query.filter(User.role.in_(("SUPER_ADMIN", "ADMIN", "DOCTOR"))).first():
            db.session.add(
                User(
                    email="verify-doctor@demo.dxcon.test",
                    role="DOCTOR",
                    password_hash=hash_password("DemoPass123!"),
                    is_active=True,
                )
            )
            db.session.commit()

        routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
        missing_web = [route for route in WEB_ROUTES if route not in routes]
        missing_api = [route for route in API_ROUTES if route not in routes]
        checks["route_registry"] = {
            "ok": not missing_web and not missing_api,
            "missing_web": missing_web,
            "missing_api": missing_api,
        }

        client = app.test_client()
        if not _login_clinical(client):
            checks["auth"] = {"ok": False, "reason": "no clinical user"}
        else:
            checks["auth"] = {"ok": True}

        web_results = {}
        web_ok = True
        for route in WEB_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200 and len(response.get_data(as_text=True)) > 200
            web_ok = web_ok and ok
            web_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["ai_clinical_dashboard"] = {"ok": web_ok, "routes": web_results}

        api_results = {}
        api_ok = True
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        from app.services.ai_clinical_service import FEATURES, dashboard_payload, interpret_results

        dashboard = dashboard_payload()
        checks["ai_provider_registry"] = {
            "ok": _api_json(client.get("/api/v1/ai-clinical/providers")).get("count", 0) >= 1
        }
        checks["prompt_registry"] = {
            "ok": _api_json(client.get("/api/v1/ai-clinical/prompts")).get("count", 0) >= 1
        }
        checks["model_router"] = {
            "ok": bool(_api_json(client.get("/api/v1/ai-clinical/router")).get("routes"))
        }

        sample_items = {
            "items": [
                {
                    "test_code": "GLU",
                    "test_name": "Glucose",
                    "result_value": "145",
                    "reference_range": "70-110",
                    "unit": "mg/dL",
                }
            ]
        }
        interpretation = _api_json(
            client.post("/api/v1/ai-clinical/interpret", json=sample_items)
        )
        checks["result_interpretation"] = {
            "ok": interpretation.get("advisory_only") is True
            and interpretation.get("human_review_required") is True
            and interpretation.get("audit_id"),
        }

        critical = _api_json(
            client.post(
                "/api/v1/ai-clinical/critical-detect",
                json={
                    "patient_id": "P-VERIFY",
                    "items": [
                        {
                            "test_code": "K",
                            "test_name": "Potassium",
                            "result_value": "6.8",
                            "reference_range": "3.5-5.1",
                            "flag": "CRITICAL",
                        }
                    ],
                },
            )
        )
        checks["critical_value_detection"] = {
            "ok": critical.get("advisory_only") is True and "alerts" in critical,
        }

        delta = _api_json(
            client.post(
                "/api/v1/ai-clinical/delta-check",
                json={
                    "patient_id": "P-VERIFY",
                    "test_code": "CREA",
                    "current_value": "1.9",
                    "previous_value": "1.2",
                },
            )
        )
        checks["delta_check"] = {
            "ok": delta.get("delta_check", {}).get("is_significant") is True,
        }

        reference = _api_json(
            client.post(
                "/api/v1/ai-clinical/reference-ranges/explain",
                json={"test_code": "GLU", "result_value": "145", "age": 45, "sex": "M"},
            )
        )
        checks["reference_range_explanation"] = {
            "ok": bool(reference.get("explanation")) and reference.get("human_review_required") is True,
        }

        summary = _api_json(client.post("/api/v1/ai-clinical/clinical-summary", json=sample_items))
        checks["clinical_summary"] = {
            "ok": summary.get("findings") and summary.get("doctor_review_required") is True,
        }

        patient = _api_json(client.post("/api/v1/ai-clinical/patient-friendly", json=sample_items))
        checks["patient_friendly_explanation"] = {
            "ok": patient.get("count", 0) >= 1 and patient.get("advisory_only") is True,
        }

        review = _api_json(client.get("/api/v1/ai-clinical/doctor-review-flag?pending_results=true"))
        checks["doctor_review_flag"] = {
            "ok": review.get("doctor_review_required") is True
            and review.get("automatic_diagnosis") is False,
        }

        audit_payload = _api_json(client.get("/api/v1/ai-clinical/audit"))
        checks["ai_audit_log"] = {"ok": audit_payload.get("count", 0) >= 1}

        usage_payload = _api_json(client.get("/api/v1/ai-clinical/usage"))
        checks["ai_usage_metrics"] = {"ok": "totals" in usage_payload}

        redact = _api_json(
            client.post(
                "/api/v1/ai-clinical/safety/redact",
                json={"text": "patient@example.com MRN: ABC12345"},
            )
        )
        checks["phi_redaction"] = {
            "ok": "[REDACTED_EMAIL]" in redact.get("redacted_text", ""),
        }

        disclaimer = _api_json(client.get("/api/v1/ai-clinical/safety/disclaimer"))
        checks["safety_disclaimer"] = {
            "ok": "advisory only" in disclaimer.get("clinical_disclaimer", "").lower(),
        }

        blocked = client.post(
            "/api/v1/ai-clinical/interpret",
            json={"items": [], "legacy": True, "test_name": "auto-diagnose without review"},
        )
        blocked_body = _api_json(blocked)
        checks["no_automatic_diagnosis"] = {
            "ok": blocked.status_code == 403 or blocked_body.get("error"),
        }

        feature_count = len(dashboard.get("features", []))
        checks["feature_coverage"] = {
            "ok": feature_count == 15 and list(FEATURES) == dashboard.get("features"),
            "features": feature_count,
        }

        direct = interpret_results(sample_items, actor="verify-script")
        checks["audit_every_output"] = {
            "ok": bool(direct.get("audit_id")) and direct.get("diagnosis_automation") is False,
        }

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "4.2",
        "sprint": "AI Clinical Platform",
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

    print(f"AI Clinical Platform score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("AI CLINICAL PLATFORM VERIFY PASS\n")
        return 0
    print("AI CLINICAL PLATFORM VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
