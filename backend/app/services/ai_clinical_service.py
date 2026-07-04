"""AI Clinical Platform business logic for Phase 4 Sprint 4.2."""

from __future__ import annotations

from typing import Any

from app.ai_platform.audit import AIAuditService
from app.ai_platform.metrics import AIUsageMetricsService
from app.ai_platform.phi_redaction import redact_phi, redact_payload
from app.ai_platform.prompt_registry import PromptRegistry
from app.ai_platform.registry import AIProviderRegistry
from app.ai_platform.router import ModelRouter
from app.ai_platform.safety import AISafetyPolicy, CLINICAL_DISCLAIMER
from app.services.ai_cds_service import (
    AIInterpretationService,
    CDSError,
    ClinicalRuleEngineService,
    CriticalDetectionService,
)
from app.services.ai_interpretation import interpret_result as legacy_interpret
from app.services.interpretation_engine_service import ReferenceRangeService
from app.services.result_flag import calculate_result_flag

CLINICAL_ROLES = ("SUPER_ADMIN", "ADMIN", "DOCTOR")

FEATURES = (
    "AI Provider Registry",
    "Prompt Registry",
    "Model Router",
    "Result Interpretation",
    "Critical Value Detection",
    "Delta Check",
    "Reference Range Explanation",
    "Clinical Summary",
    "Patient-Friendly Explanation",
    "Doctor Review Flag",
    "AI Audit Log",
    "AI Usage Metrics",
    "PHI Redaction",
    "Safety Disclaimer",
    "Verification Report",
)

ROUTER_TASK_TYPES = ("interpretation", "summary", "risk", "reference_range", "patient_friendly", "general")


class AIClinicalError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def ensure_clinical() -> dict[str, Any]:
    AIProviderRegistry.ensure_defaults()
    PromptRegistry.ensure_defaults()
    ClinicalRuleEngineService.ensure_default_packs()
    return {"ready": True}


def _audit(action: str, resource_type: str, detail: dict | None = None, *, actor: str | None = None, resource_id: str | None = None):
    return AIAuditService.write(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail or {},
        actor=actor or "SYSTEM",
    )


def _wrap_advisory(payload: dict[str, Any], *, task_type: str = "general") -> dict[str, Any]:
    wrapped = AISafetyPolicy.wrap_output(payload, task_type=task_type)
    wrapped["doctor_review_required"] = True
    wrapped["diagnosis_automation"] = False
    return wrapped


def dashboard_payload() -> dict[str, Any]:
    ensure_clinical()
    providers = AIProviderRegistry.list_providers()
    prompts = PromptRegistry.list_prompts()
    audit = AIAuditService.list_entries(page_size=5)
    usage = AIUsageMetricsService.summary()
    return {
        "platform": "AI Clinical Platform",
        "phase": "4.2",
        "sprint": "AI Clinical Platform",
        "status": "OK",
        "policy": {
            "advisory_only": True,
            "automatic_diagnosis": False,
            "human_review_required": True,
            "clinical_disclaimer": CLINICAL_DISCLAIMER,
        },
        "summary": {
            "providers": providers["count"],
            "prompts": prompts["count"],
            "audit_entries": audit["count"],
            "usage_records": usage["count"],
            "router_tasks": len(ROUTER_TASK_TYPES),
        },
        "features": list(FEATURES),
    }


def list_providers() -> dict[str, Any]:
    ensure_clinical()
    return AIProviderRegistry.list_providers()


def list_prompts() -> dict[str, Any]:
    ensure_clinical()
    return PromptRegistry.list_prompts()


def model_router_payload(task_type: str | None = None) -> dict[str, Any]:
    ensure_clinical()
    tasks = [task_type] if task_type else list(ROUTER_TASK_TYPES)
    routes = {}
    for task in tasks:
        route = ModelRouter.route(task)
        routes[task] = {
            "provider_type": route["provider_type"],
            "provider_label": getattr(route["provider"], "provider_label", route["provider_type"]),
        }
    return {
        "default_routes": ModelRouter.DEFAULT_ROUTES,
        "routes": routes,
        "advisory_only": True,
    }


def interpret_results(data: dict[str, Any], *, actor: str | None = None) -> dict[str, Any]:
    ensure_clinical()
    safety = AISafetyPolicy.check_request("interpretation", data)
    if not safety.get("allowed"):
        raise AIClinicalError(safety.get("message", "Blocked by safety policy"), 403)
    try:
        if data.get("legacy"):
            text = legacy_interpret(
                data.get("test_name"),
                data.get("result_value"),
                data.get("reference_range"),
                data.get("flag"),
            )
            payload = {
                "interpretations": [
                    {
                        "test_name": data.get("test_name"),
                        "result_value": data.get("result_value"),
                        "explanation": text,
                        "doctor_review_required": True,
                    }
                ],
                "count": 1,
            }
        else:
            payload = AIInterpretationService.interpret_payload(data)
    except CDSError as exc:
        raise AIClinicalError(exc.message, exc.status_code) from exc
    wrapped = _wrap_advisory(payload, task_type="interpretation")
    audit = _audit(
        "RESULT_INTERPRETATION",
        "LabInterpretation",
        {"count": wrapped.get("count", 0)},
        actor=actor,
    )
    wrapped["audit_id"] = audit["id"]
    AIUsageMetricsService.record(provider_id=None, task_type="interpretation", requests=1)
    return wrapped


def detect_critical_values(data: dict[str, Any], *, actor: str | None = None) -> dict[str, Any]:
    ensure_clinical()
    if not data.get("items"):
        raise AIClinicalError("items is required", 400)
    payload = CriticalDetectionService.detect(data)
    wrapped = _wrap_advisory(payload, task_type="risk")
    audit = _audit(
        "CRITICAL_VALUE_DETECTION",
        "CriticalAlert",
        {"count": wrapped.get("count", 0)},
        actor=actor,
    )
    wrapped["audit_id"] = audit["id"]
    AIUsageMetricsService.record(provider_id=None, task_type="risk", requests=1)
    return wrapped


def delta_check(data: dict[str, Any], *, actor: str | None = None) -> dict[str, Any]:
    ensure_clinical()
    required = ("patient_id", "test_code", "current_value", "previous_value")
    missing = [field for field in required if not data.get(field)]
    if missing:
        raise AIClinicalError(f"Missing fields: {', '.join(missing)}", 400)
    result = ClinicalRuleEngineService.evaluate_delta(
        data["patient_id"],
        data["test_code"],
        data["current_value"],
        data["previous_value"],
        threshold_percent=int(data.get("threshold_percent") or 20),
    )
    if result is None:
        raise AIClinicalError("Unable to evaluate delta check with supplied values", 400)
    payload = {"delta_check": result, "advisory_only": True}
    wrapped = _wrap_advisory(payload, task_type="interpretation")
    audit = _audit(
        "DELTA_CHECK",
        "ClinicalDeltaCheck",
        {"check_code": result.get("check_code"), "significant": result.get("is_significant")},
        actor=actor,
        resource_id=result.get("id"),
    )
    wrapped["audit_id"] = audit["id"]
    return wrapped


def explain_reference_range(data: dict[str, Any], *, actor: str | None = None) -> dict[str, Any]:
    ensure_clinical()
    test_code = data.get("test_code")
    if not test_code:
        raise AIClinicalError("test_code is required", 400)
    age = data.get("age")
    sex = data.get("sex")
    result_value = data.get("result_value")
    row = ReferenceRangeService.resolve(test_code, test_name=data.get("test_name"), age=age, sex=sex)
    ranges = ClinicalRuleEngineService.list_reference_ranges(test_code=test_code, sex=sex, age=age)
    range_text = row.as_range_text() if row else None
    if not range_text and ranges:
        first = ranges[0]
        low = first.get("low_value")
        high = first.get("high_value")
        if low is not None and high is not None:
            range_text = f"{low}-{high}"
        elif first.get("reference_range"):
            range_text = first.get("reference_range")
    flag = calculate_result_flag(result_value, range_text) if range_text and result_value is not None else "UNKNOWN"
    explanation = (
        f"Advisory: {test_code} reference range is {range_text}. "
        f"The supplied result {result_value} appears {flag.lower()} relative to the reference range. "
        "Clinical review is required before action."
        if range_text
        else f"Advisory: no active reference range found for {test_code}. Physician review recommended."
    )
    payload = {
        "test_code": test_code,
        "reference_range": range_text,
        "result_value": result_value,
        "flag": flag,
        "explanation": explanation,
        "ranges": ranges[:5],
    }
    wrapped = _wrap_advisory(payload, task_type="reference_range")
    audit = _audit("REFERENCE_RANGE_EXPLANATION", "ReferenceRange", {"test_code": test_code}, actor=actor)
    wrapped["audit_id"] = audit["id"]
    return wrapped


def clinical_summary(data: dict[str, Any], *, actor: str | None = None) -> dict[str, Any]:
    ensure_clinical()
    interpretation = interpret_results(data, actor=actor)
    items = interpretation.get("interpretations") or []
    abnormal = [item for item in items if item.get("abnormal_findings")]
    critical = [item for item in items if item.get("is_critical")]
    risk_level = "LOW"
    if critical:
        risk_level = "CRITICAL"
    elif abnormal:
        risk_level = "MEDIUM"
    findings = [item.get("explanation") for item in abnormal] or [
        "No significant abnormal laboratory pattern detected in advisory review."
    ]
    payload = {
        "risk_level": risk_level,
        "findings": findings,
        "recommendations": [
            "Advisory output only — physician review required before clinical action.",
            "Correlate with symptoms, medications, and prior results.",
        ],
        "items_reviewed": len(items),
    }
    wrapped = _wrap_advisory(payload, task_type="summary")
    audit = _audit(
        "CLINICAL_SUMMARY",
        "ClinicalSummary",
        {"risk_level": risk_level, "items_reviewed": len(items)},
        actor=actor,
    )
    wrapped["audit_id"] = audit["id"]
    AIUsageMetricsService.record(provider_id=None, task_type="summary", requests=1)
    return wrapped


def _plain_language(text: str) -> str:
    replacements = {
        "Clinical correlation recommended": "Your doctor may want to discuss this result with you.",
        "clinical correlation": "talk with your doctor",
        "Advisory:": "Note:",
        "bac si": "doctor",
        "bác sĩ": "doctor",
    }
    output = text or "Your test result should be reviewed by your doctor."
    for src, dst in replacements.items():
        output = output.replace(src, dst)
    return output


def patient_friendly_explanation(data: dict[str, Any], *, actor: str | None = None) -> dict[str, Any]:
    ensure_clinical()
    interpretation = AIInterpretationService.interpret_payload(data)
    explanations = []
    for item in interpretation.get("interpretations") or []:
        clinical_text = item.get("explanation") or ""
        explanations.append(
            {
                "test_name": item.get("test_name"),
                "plain_language": _plain_language(clinical_text),
                "doctor_review_required": True,
                "is_critical": item.get("is_critical", False),
            }
        )
    payload = {
        "count": len(explanations),
        "explanations": explanations,
        "patient_notice": "This explanation is for patient education only and is not a diagnosis.",
    }
    wrapped = _wrap_advisory(payload, task_type="patient_friendly")
    audit = _audit(
        "PATIENT_FRIENDLY_EXPLANATION",
        "PatientExplanation",
        {"count": len(explanations)},
        actor=actor,
    )
    wrapped["audit_id"] = audit["id"]
    AIUsageMetricsService.record(provider_id=None, task_type="patient_friendly", requests=1)
    return wrapped


def doctor_review_flag(data: dict[str, Any] | None = None) -> dict[str, Any]:
    ensure_clinical()
    pending_review = bool((data or {}).get("pending_results"))
    payload = {
        "doctor_review_required": True,
        "human_review_required": True,
        "review_status": "PENDING" if pending_review else "REQUIRED",
        "automation_level": "advisory",
        "automatic_diagnosis": False,
        "clinical_disclaimer": CLINICAL_DISCLAIMER,
    }
    return _wrap_advisory(payload, task_type="general")


def list_audit(*, page: int = 1, page_size: int = 50) -> dict[str, Any]:
    ensure_clinical()
    return AIAuditService.list_entries(page=page, page_size=page_size)


def usage_metrics() -> dict[str, Any]:
    ensure_clinical()
    return AIUsageMetricsService.summary()


def phi_redaction_demo(text: str, *, actor: str | None = None) -> dict[str, Any]:
    ensure_clinical()
    redacted = redact_phi(text or "")
    payload = {"original_length": len(text or ""), "redacted_text": redacted}
    wrapped = _wrap_advisory(payload, task_type="general")
    audit = _audit("PHI_REDACTION", "PHI", {"redacted": True}, actor=actor)
    wrapped["audit_id"] = audit["id"]
    return wrapped


def safety_disclaimer() -> dict[str, Any]:
    ensure_clinical()
    return doctor_review_flag()


def analyze_lab_payload(data: dict[str, Any], *, actor: str | None = None) -> dict[str, Any]:
    """Run advisory interpretation, critical detection, and summary in one audited call."""
    ensure_clinical()
    redacted = redact_payload(data or {})
    interpretation = interpret_results(redacted, actor=actor)
    critical = detect_critical_values(redacted, actor=actor) if redacted.get("items") else {"count": 0, "alerts": []}
    summary = clinical_summary(redacted, actor=actor)
    return {
        "interpretation": interpretation,
        "critical_detection": critical,
        "clinical_summary": summary,
        "doctor_review_required": True,
        "clinical_disclaimer": CLINICAL_DISCLAIMER,
    }
