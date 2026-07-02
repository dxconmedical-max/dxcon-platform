from flask import Blueprint, request

from app.ai_platform.audit import AIAuditService
from app.ai_platform.inference_service import AIPlatformError, InferenceService
from app.ai_platform.metrics import AIUsageMetricsService
from app.ai_platform.registry import AIProviderRegistry
from app.ai_platform.prompt_registry import PromptRegistry


ai_platform_bp = Blueprint("ai_platform", __name__, url_prefix="/api/v1/ai-platform")


def _actor():
    return request.headers.get("X-User-Email", "SYSTEM")


def _error(exc):
    return {"error": exc.message}, exc.status_code


@ai_platform_bp.route("/providers", methods=["GET"])
def list_providers():
    return AIProviderRegistry.list_providers()


@ai_platform_bp.route("/providers", methods=["POST"])
def register_provider():
    data = request.get_json(silent=True) or {}
    try:
        return AIProviderRegistry.register(data), 201
    except ValueError as exc:
        return {"error": str(exc)}, 400


@ai_platform_bp.route("/prompts", methods=["GET"])
def list_prompts():
    return PromptRegistry.list_prompts()


@ai_platform_bp.route("/prompts", methods=["POST"])
def register_prompt():
    data = request.get_json(silent=True) or {}
    try:
        return PromptRegistry.register(data), 201
    except ValueError as exc:
        return {"error": str(exc)}, 400


@ai_platform_bp.route("/infer", methods=["POST"])
def infer():
    data = request.get_json(silent=True) or {}
    try:
        return InferenceService.queue_inference(data, actor=_actor())
    except AIPlatformError as exc:
        return _error(exc)


@ai_platform_bp.route("/audit", methods=["GET"])
def list_audit():
    page = max(int(request.args.get("page", 1)), 1)
    page_size = min(max(int(request.args.get("page_size", 50)), 1), 200)
    return AIAuditService.list_entries(
        action=request.args.get("action"),
        resource_type=request.args.get("resource_type"),
        page=page,
        page_size=page_size,
    )


@ai_platform_bp.route("/usage", methods=["GET"])
def usage_metrics():
    return AIUsageMetricsService.summary()
