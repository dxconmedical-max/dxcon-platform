import json
import uuid
from datetime import datetime

from app.ai_platform.audit import AIAuditService
from app.ai_platform.metrics import AIUsageMetricsService
from app.ai_platform.models import AIInferenceJob
from app.ai_platform.phi_redaction import redact_payload
from app.ai_platform.prompt_registry import PromptRegistry
from app.ai_platform.registry import AIProviderRegistry
from app.ai_platform.router import ModelRouter
from app.ai_platform.safety import AISafetyPolicy
from app.extensions.db import db


class AIPlatformError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class InferenceService:
    @staticmethod
    def queue_inference(data, actor="SYSTEM"):
        task_type = data.get("task_type") or "general"
        safety = AISafetyPolicy.check_request(task_type, data.get("input") or {})
        if not safety.get("allowed"):
            raise AIPlatformError(safety.get("message"), 403)

        prompt_code = data.get("prompt_code")
        prompt_id = data.get("prompt_id")
        prompt_version = None
        template_text = data.get("prompt_text")

        if prompt_code:
            prompt, version = PromptRegistry.get_by_code(prompt_code)
            prompt_id = prompt.id
            prompt_version = version.version
            template_text = version.template_text
        elif prompt_id:
            prompt, version = PromptRegistry.get_active_version(prompt_id)
            prompt_version = version.version
            template_text = version.template_text

        provider_id = data.get("provider_id")
        provider_type = data.get("provider_type")
        if provider_id:
            provider_row = AIProviderRegistry.get_provider_row(provider_id)
            provider_type = provider_row.provider_type
        route = ModelRouter.route(task_type, provider_type)
        provider_type = route["provider_type"]

        redacted_input = redact_payload(data.get("input") or {})
        job = AIInferenceJob(
            job_code=data.get("job_code") or f"AIJ-{uuid.uuid4().hex[:8].upper()}",
            provider_id=provider_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            input_json=json.dumps(redacted_input),
            status="QUEUED",
            human_review_required=True,
        )
        db.session.add(job)
        db.session.commit()

        AIAuditService.write(
            action="INFERENCE_QUEUED",
            resource_type="AIInferenceJob",
            resource_id=job.id,
            detail={"task_type": task_type, "provider_type": provider_type},
            actor=actor,
        )

        async_mode = data.get("async", True)
        if async_mode:
            from app.ai_platform.inference import process_inference_job_async

            process_inference_job_async(job.id, template_text, task_type, provider_type)
            return {"job": job.to_dict(), "queued": True, "status": "QUEUED"}

        return InferenceService.run_job(job.id, template_text, task_type, provider_type)

    @staticmethod
    def run_job(job_id, template_text=None, task_type="general", provider_type="LOCAL"):
        job = AIInferenceJob.query.filter_by(id=job_id).first()
        if job is None:
            raise AIPlatformError("Inference job not found", 404)

        job.status = "PROCESSING"
        db.session.commit()

        provider = AIProviderRegistry.get_instance(provider_type)
        input_data = json.loads(job.input_json or "{}")
        raw_output = provider.infer(template_text or "Provide advisory output.", input_data)
        output = AISafetyPolicy.wrap_output(raw_output, task_type=task_type)

        job.output_json = json.dumps(output)
        job.status = "COMPLETED"
        job.human_review_required = True
        job.completed_at = datetime.utcnow()
        db.session.commit()

        AIUsageMetricsService.record(
            provider_id=job.provider_id,
            task_type=task_type,
            tokens_in=raw_output.get("tokens_in", 0),
            tokens_out=raw_output.get("tokens_out", 0),
        )
        AIAuditService.write(
            action="INFERENCE_COMPLETED",
            resource_type="AIInferenceJob",
            resource_id=job.id,
            detail={"task_type": task_type, "provider_type": provider_type},
        )
        return {"job": job.to_dict(), "output": output, "queued": False, "status": "COMPLETED"}
