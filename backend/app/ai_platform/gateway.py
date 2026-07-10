"""AI Platform gateway — single approved inference entrypoint."""

from __future__ import annotations

from app.ai_platform.governance import AIGovernanceService
from app.ai_platform.inference_service import AIPlatformError, InferenceService
from app.ai_platform.phi_redaction import redact_payload
from app.ai_platform.rag import AIRagService
from app.ai_platform.safety import AISafetyPolicy


class AIGateway:
    @staticmethod
    def infer(
        data: dict,
        *,
        actor: str = "SYSTEM",
        organization_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> dict:
        task_type = data.get("task_type") or "general"
        gov = AIGovernanceService.evaluate_request(task_type, organization_id)
        if not gov.get("allowed"):
            raise AIPlatformError(gov.get("message", "Blocked by governance"), 403)

        safety = AISafetyPolicy.check_request(task_type, data.get("input") or {})
        if not safety.get("allowed"):
            raise AIPlatformError(safety.get("message"), 403)

        payload = dict(data)
        if gov.get("phi_redaction_required", True):
            payload["input"] = redact_payload(payload.get("input") or {})

        if data.get("use_rag") and data.get("rag_query"):
            rag = AIRagService.retrieve(data["rag_query"], organization_id=organization_id)
            rag_context = "\n".join(c["content"] for c in rag.get("chunks", []))
            input_data = payload.get("input") or {}
            input_data["rag_context"] = rag_context
            input_data["rag_citations"] = rag.get("chunks", [])
            payload["input"] = input_data

        payload["organization_id"] = organization_id
        payload["user_id"] = user_id
        payload["session_id"] = session_id
        return InferenceService.queue_inference(payload, actor=actor)
