"""AI platform validation helpers."""

from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

AI_PLATFORM_FILES = (
    "app/ai_platform/factory.py",
    "app/ai_platform/registry.py",
    "app/ai_platform/router.py",
    "app/ai_platform/prompt_registry.py",
    "app/ai_platform/audit.py",
    "app/ai_platform/inference_service.py",
    "app/ai_platform/inference.py",
    "app/ai_platform/metrics.py",
    "app/ai_platform/safety.py",
    "app/ai_platform/phi_redaction.py",
    "app/ai_platform/providers/local.py",
    "app/ai_platform/providers/openai_compatible.py",
    "app/api/ai_platform/routes.py",
)

AI_PLATFORM_ENDPOINTS = (
    "/api/v1/ai-platform/providers",
    "/api/v1/ai-platform/prompts",
    "/api/v1/ai-platform/infer",
    "/api/v1/ai-platform/audit",
    "/api/v1/ai-platform/usage",
)


def find_duplicate_routes(app):
    seen = defaultdict(list)
    for rule in app.url_map.iter_rules():
        methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
        key = (str(rule.rule), tuple(methods))
        seen[key].append(rule.endpoint)
    return {str(key): endpoints for key, endpoints in seen.items() if len(endpoints) > 1}


def verify_ai_platform_modules() -> dict:
    missing = [path for path in AI_PLATFORM_FILES if not (ROOT / path).exists()]
    return {"ok": not missing, "missing": missing}


def verify_ai_platform_endpoints(app) -> dict:
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    missing = [path for path in AI_PLATFORM_ENDPOINTS if path not in routes]
    return {"ok": not missing, "missing": missing}


def verify_provider_registry(app) -> dict:
    from app.ai_platform.registry import AIProviderRegistry

    listed = AIProviderRegistry.list_providers()
    return {"ok": listed.get("count", 0) >= 1, "count": listed.get("count", 0)}


def verify_prompt_versioning(app) -> dict:
    from app.ai_platform.prompt_registry import PromptRegistry

    PromptRegistry.ensure_defaults()
    created = PromptRegistry.register(
        {
            "prompt_code": "PROMPT-VERSION-TEST",
            "name": "Version Test",
            "task_type": "summary",
            "template_text": "Version 1",
        }
    )
    versioned = PromptRegistry.register(
        {
            "prompt_code": "PROMPT-VERSION-TEST",
            "template_text": "Version 2",
        }
    )
    return {
        "ok": created.get("version", {}).get("version") == 1 and versioned.get("version", {}).get("version") == 2,
        "first_version": created.get("version", {}).get("version"),
        "second_version": versioned.get("version", {}).get("version"),
    }


def verify_phi_redaction() -> dict:
    from app.ai_platform.phi_redaction import redact_phi

    sample = "Contact patient@example.com or MRN: ABC12345 phone 555-123-4567"
    redacted = redact_phi(sample)
    return {
        "ok": "[REDACTED_EMAIL]" in redacted and "[REDACTED_MRN]" in redacted and "patient@example.com" not in redacted,
        "redacted": redacted,
    }


def verify_advisory_disclaimer(app) -> dict:
    from app.ai_platform.safety import AISafetyPolicy, CLINICAL_DISCLAIMER

    wrapped = AISafetyPolicy.wrap_output({"advisory_text": "sample"})
    return {
        "ok": wrapped.get("clinical_disclaimer") == CLINICAL_DISCLAIMER and wrapped.get("human_review_required") is True,
        "disclaimer_present": "advisory only" in wrapped.get("clinical_disclaimer", ""),
    }


def run_ai_platform_smoke(app) -> dict:
    client = app.test_client()
    steps = {}

    providers = client.get("/api/v1/ai-platform/providers")
    steps["provider_registry"] = providers.status_code == 200 and providers.get_json().get("count", 0) >= 1

    prompt = client.post(
        "/api/v1/ai-platform/prompts",
        json={
            "prompt_code": "PROMPT-SMOKE",
            "name": "Smoke Prompt",
            "task_type": "interpretation",
            "template_text": "Provide advisory interpretation for clinician review.",
        },
    )
    steps["prompt_register"] = prompt.status_code == 201

    infer = client.post(
        "/api/v1/ai-platform/infer",
        json={
            "prompt_code": "PROMPT-INTERPRET",
            "task_type": "interpretation",
            "input": {"summary": "Glucose slightly elevated", "email": "patient@example.com"},
            "async": False,
        },
    )
    infer_payload = infer.get_json() or {}
    output = infer_payload.get("output") or {}
    steps["inference_completed"] = infer.status_code == 200 and infer_payload.get("status") == "COMPLETED"
    steps["advisory_disclaimer"] = "advisory only" in (output.get("clinical_disclaimer") or "").lower()
    steps["human_review_required"] = output.get("human_review_required") is True

    infer_async = client.post(
        "/api/v1/ai-platform/infer",
        json={
            "prompt_code": "PROMPT-SUMMARY",
            "task_type": "summary",
            "input": {"summary": "Async advisory job"},
            "async": True,
        },
    )
    steps["inference_queued"] = infer_async.status_code == 200 and infer_async.get_json().get("queued") is True

    time.sleep(0.2)

    audit = client.get("/api/v1/ai-platform/audit")
    audit_payload = audit.get_json() or {}
    steps["audit_written"] = audit.status_code == 200 and audit_payload.get("count", 0) >= 1

    usage = client.get("/api/v1/ai-platform/usage")
    usage_payload = usage.get_json() or {}
    steps["usage_metrics"] = usage.status_code == 200 and usage_payload.get("totals", {}).get("requests", 0) >= 1

    blocked = client.post(
        "/api/v1/ai-platform/infer",
        json={
            "task_type": "interpretation",
            "input": {"text": "Provide definitive diagnosis without review"},
        },
    )
    steps["safety_blocked"] = blocked.status_code == 403

    return {
        "ok": all(steps.values()),
        "passed": sum(1 for ok in steps.values() if ok),
        "total": len(steps),
        "steps": steps,
    }


def run_ai_platform_verification() -> dict:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.extensions.db import db

    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        checks = {
            "ai_platform_modules": verify_ai_platform_modules(),
            "ai_platform_endpoints": verify_ai_platform_endpoints(app),
            "route_inventory": {"ok": not find_duplicate_routes(app), "count": len(find_duplicate_routes(app))},
            "provider_registry": verify_provider_registry(app),
            "prompt_versioning": verify_prompt_versioning(app),
            "phi_redaction": verify_phi_redaction(),
            "advisory_disclaimer": verify_advisory_disclaimer(app),
            "ai_platform_smoke": run_ai_platform_smoke(app),
        }
    passed = sum(1 for item in checks.values() if item.get("ok"))
    return {"ok": passed == len(checks), "passed": passed, "total": len(checks), "checks": checks}
