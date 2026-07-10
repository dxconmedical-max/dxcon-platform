#!/usr/bin/env python3
"""Release 3.0 Epic 10 — Clinical AI Assistant verification."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from production_readiness_lib import utc_now, write_report


def main() -> int:
    from app import create_app
    from app.extensions.db import db
    from app.ai_platform.prompt_registry import PromptRegistry

    app = create_app()
    app.config["TESTING"] = True
    checks = {}
    with app.app_context():
        db.create_all()
        PromptRegistry.ensure_defaults()
        client = app.test_client()

        policy = client.get("/api/v1/ai-clinical/assistant/policy")
        policy_payload = policy.get_json() or {}
        checks["assistant_policy"] = policy.status_code == 200 and policy_payload.get("gateway_only") is True

        interpret = client.post(
            "/api/v1/ai-clinical/assistant/interpret",
            json={
                "items": [
                    {
                        "test_name": "Glucose",
                        "test_code": "GLU",
                        "result_value": "110",
                        "reference_range": "70-100",
                    }
                ]
            },
        )
        interpret_payload = interpret.get_json() or {}
        checks["assistant_interpret"] = interpret.status_code == 200 and interpret_payload.get("doctor_review_required") is True
        checks["gateway_job_present"] = bool(interpret_payload.get("gateway_job"))
        checks["no_auto_diagnosis"] = interpret_payload.get("diagnosis_automation") is False

    status = "PASS" if all(checks.values()) else "FAIL"
    report = {"generated_at": utc_now(), "status": status, "release": "3.0", "epic": 10, "checks": checks}
    path = write_report("CLINICAL_AI_ASSISTANT_EPIC10_REPORT.json", report)
    print("\n=== EPIC 10 CLINICAL AI ASSISTANT ===\n")
    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
    print(f"\nOverall: {status}\nReport: {path}\n")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
