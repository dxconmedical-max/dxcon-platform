"""Clinical AI Assistant — Release 3.0 Epic 10.

All advisory LLM inference must go through the approved AI Gateway.
Physician review is always required for clinical recommendations.
"""

from __future__ import annotations

from typing import Any

from app.ai_platform.audit import AIAuditService
from app.ai_platform.gateway import AIGateway
from app.ai_platform.inference_service import AIPlatformError
from app.ai_platform.safety import CLINICAL_DISCLAIMER, AISafetyPolicy
from app.services.ai_cds_service import AIInterpretationService, CDSError, CriticalDetectionService


class ClinicalAssistantError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _wrap_clinical(payload: dict[str, Any], *, task_type: str = "interpretation") -> dict[str, Any]:
    wrapped = AISafetyPolicy.wrap_output(payload, task_type=task_type)
    wrapped["doctor_review_required"] = True
    wrapped["diagnosis_automation"] = False
    wrapped["gateway_only"] = True
    return wrapped


def assistant_interpret(data: dict[str, Any], *, actor: str | None = None, organization_id: str | None = None, user_id: str | None = None) -> dict[str, Any]:
    """Interpret lab results using CDS rules plus gateway-backed advisory enrichment."""
    if data.get("legacy"):
        from app.services.ai_interpretation import interpret_result as legacy_interpret

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
        return _wrap_clinical(payload, task_type="interpretation")

    try:
        cds_payload = AIInterpretationService.interpret_payload(data)
    except CDSError as exc:
        raise ClinicalAssistantError(exc.message, exc.status_code) from exc

    gateway_result = AIGateway.infer(
        {
            "prompt_code": "PROMPT-INTERPRET",
            "task_type": "interpretation",
            "input": {"cds_summary": cds_payload, "items": data.get("items") or []},
            "async": False,
        },
        actor=actor or "SYSTEM",
        organization_id=organization_id,
        user_id=user_id,
    )
    output = gateway_result.get("output") or {}
    payload = {
        "interpretations": cds_payload.get("interpretations") or [],
        "count": cds_payload.get("count", 0),
        "advisory_enrichment": output.get("advisory_text") or output.get("text"),
        "gateway_job": gateway_result.get("job"),
    }
    wrapped = _wrap_clinical(payload, task_type="interpretation")
    audit = AIAuditService.write(
        action="CLINICAL_ASSISTANT_INTERPRET",
        resource_type="ClinicalAssistant",
        detail={"count": wrapped.get("count", 0), "gateway_only": True},
        actor=actor or "SYSTEM",
    )
    wrapped["audit_id"] = audit["id"]
    return wrapped


def assistant_critical_review(data: dict[str, Any], *, actor: str | None = None) -> dict[str, Any]:
    if not data.get("items"):
        raise ClinicalAssistantError("items is required", 400)
    cds = CriticalDetectionService.detect(data)
    gateway = AIGateway.infer(
        {
            "prompt_code": "PROMPT-SUMMARY",
            "task_type": "risk",
            "input": {"critical_alerts": cds.get("alerts", [])},
            "async": False,
        },
        actor=actor or "SYSTEM",
    )
    payload = {**cds, "advisory_summary": (gateway.get("output") or {}).get("advisory_text")}
    wrapped = _wrap_clinical(payload, task_type="risk")
    wrapped["doctor_review_required"] = True
    return wrapped


def assistant_policy() -> dict[str, Any]:
    return {
        "advisory_only": True,
        "automatic_diagnosis": False,
        "doctor_review_required": True,
        "gateway_only": True,
        "clinical_disclaimer": CLINICAL_DISCLAIMER,
        "note": "AI never replaces physicians. Use approved AI Gateway only.",
    }
