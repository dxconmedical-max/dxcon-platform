from app.core.background_tasks import background_tasks


def process_inference_job_async(job_id, template_text, task_type, provider_type):
    def _run():
        from app.ai_platform.inference_service import InferenceService

        InferenceService.run_job(job_id, template_text, task_type, provider_type)

    return background_tasks.submit(_run)
