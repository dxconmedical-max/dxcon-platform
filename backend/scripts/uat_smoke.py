#!/usr/bin/env python3
"""Staging UAT smoke — user journey and API health checks."""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


def _response_payload(response):
    payload = response.get_json() or {}
    if isinstance(payload.get("data"), dict) and payload.get("success") is True:
        return payload["data"]
    return payload


def run_uat_smoke():
    from app import create_app
    from app.extensions.db import db
    from scripts.staging_stack_lib import parse_env_file

    staging_values = parse_env_file(ROOT / ".env.staging.example")
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "APP_ENV": "staging",
            "CORS_ORIGINS": staging_values.get("CORS_ORIGINS", ""),
            "SQLALCHEMY_DATABASE_URI": staging_values.get("DATABASE_URL", ""),
            "REDIS_URL": staging_values.get("REDIS_URL", ""),
            "SMTP_HOST": staging_values.get("SMTP_HOST", ""),
            "STORAGE_PATH": staging_values.get("STORAGE_PATH", "/tmp/dxcon-uploads"),
        }
    )
    client = app.test_client()
    steps = {}

    with app.app_context():
        db.create_all()

        steps["live"] = client.get("/live").status_code == 200
        steps["ready"] = client.get("/ready").status_code == 200
        steps["system_health"] = client.get("/api/v1/system/health").status_code == 200
        steps["system_liveness"] = client.get("/api/v1/system/liveness").status_code == 200
        steps["system_metrics"] = client.get("/api/v1/system/metrics").status_code in {200, 404}

        register = client.post(
            "/api/v1/auth/register",
            json={"email": "uat@dxcon.test", "password": "SecurePass123!", "role": "ADMIN"},
        )
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "uat@dxcon.test", "password": "SecurePass123!"},
        )
        login_payload = _response_payload(login)
        steps["register_login"] = login.status_code == 200 and bool(login_payload.get("access_token"))

        token = login_payload.get("access_token", "")
        patient = client.post(
            "/api/v1/patients",
            json={
                "patient_code": f"UAT-{uuid.uuid4().hex[:6].upper()}",
                "full_name": "UAT Patient",
                "gender": "F",
                "phone": "0909111222",
                "email": "uat-patient@dxcon.test",
            },
            headers={"Authorization": f"Bearer {token}"} if token else {},
        )
        patient_payload = _response_payload(patient)
        patient_id = (patient_payload.get("patient") or patient_payload).get("id")
        steps["create_patient"] = patient.status_code == 201 and bool(patient_id)

        patients = client.get("/api/v1/patients")
        patients_payload = _response_payload(patients)
        steps["list_patients"] = patients.status_code == 200 and patients_payload.get("count", 0) >= 0

    passed = sum(1 for ok in steps.values() if ok)
    return {
        "ok": passed == len(steps),
        "passed": passed,
        "total": len(steps),
        "steps": steps,
    }


def main():
    print("\n=== DXCON STAGING UAT SMOKE ===\n")
    result = run_uat_smoke()
    for name, ok in result["steps"].items():
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
    print(f"\nUAT: {result['passed']}/{result['total']}")
    if not result["ok"]:
        sys.exit(1)
    print("STAGING UAT SMOKE PASSED\n")


if __name__ == "__main__":
    main()
