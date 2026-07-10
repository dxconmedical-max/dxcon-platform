"""AI Platform routes — Release 3.0 Epic 9."""

from flask import Blueprint, request

from app.ai_platform.audit import AIAuditService
from app.ai_platform.gateway import AIGateway
from app.ai_platform.governance import AIGovernanceService
from app.ai_platform.inference_service import AIPlatformError
from app.ai_platform.memory import AIMemoryError, AIMemoryService
from app.ai_platform.metrics import AIUsageMetricsService
from app.ai_platform.rag import AIRagError, AIRagService
from app.ai_platform.registry import AIProviderRegistry
from app.ai_platform.prompt_registry import PromptRegistry
from app.ai_platform.security import ai_admin_required, ai_gateway_required, ai_infer_required


ai_platform_bp = Blueprint("ai_platform", __name__, url_prefix="/api/v1/ai-platform")


def _actor():
    ctx = getattr(request, "ai_context", None) or {}
    return ctx.get("email") or request.headers.get("X-User-Email", "SYSTEM")


def _ctx():
    return getattr(request, "ai_context", None) or {}


def _error(exc):
    return {"error": exc.message}, exc.status_code


@ai_platform_bp.route("/providers", methods=["GET"])
@ai_gateway_required()
def list_providers():
    return AIProviderRegistry.list_providers()


@ai_platform_bp.route("/providers", methods=["POST"])
@ai_admin_required
def register_provider():
    data = request.get_json(silent=True) or {}
    try:
        return AIProviderRegistry.register(data), 201
    except ValueError as exc:
        return {"error": str(exc)}, 400


@ai_platform_bp.route("/prompts", methods=["GET"])
@ai_gateway_required()
def list_prompts():
    return PromptRegistry.list_prompts()


@ai_platform_bp.route("/prompts", methods=["POST"])
@ai_admin_required
def register_prompt():
    data = request.get_json(silent=True) or {}
    try:
        return PromptRegistry.register(data), 201
    except ValueError as exc:
        return {"error": str(exc)}, 400


@ai_platform_bp.route("/infer", methods=["POST"])
@ai_infer_required
def infer():
    data = request.get_json(silent=True) or {}
    ctx = _ctx()
    try:
        return AIGateway.infer(
            data,
            actor=_actor(),
            organization_id=ctx.get("organization_id"),
            user_id=ctx.get("user_id"),
            session_id=data.get("session_id"),
        )
    except AIPlatformError as exc:
        return _error(exc)


@ai_platform_bp.route("/governance", methods=["GET"])
@ai_gateway_required()
def list_governance():
    return AIGovernanceService.list_policies()


@ai_platform_bp.route("/governance", methods=["POST"])
@ai_admin_required
def upsert_governance():
    return AIGovernanceService.upsert_policy(request.get_json(silent=True) or {}), 200


@ai_platform_bp.route("/memory/sessions", methods=["POST"])
@ai_infer_required
def create_memory_session():
    ctx = _ctx()
    return AIMemoryService.create_session(
        organization_id=ctx.get("organization_id"),
        user_id=ctx.get("user_id"),
        context_type=(request.get_json(silent=True) or {}).get("context_type", "GENERAL"),
    ), 201


@ai_platform_bp.route("/memory/sessions/<session_id>", methods=["GET"])
@ai_infer_required
def get_memory_session(session_id: str):
    try:
        return AIMemoryService.get_session(session_id), 200
    except AIMemoryError as exc:
        return {"error": str(exc)}, 404


@ai_platform_bp.route("/memory/sessions/<session_id>/messages", methods=["POST"])
@ai_infer_required
def append_memory_message(session_id: str):
    payload = request.get_json(silent=True) or {}
    try:
        return AIMemoryService.append_message(session_id, payload.get("role", "user"), payload.get("content", "")), 201
    except AIMemoryError as exc:
        return {"error": str(exc)}, 400


@ai_platform_bp.route("/rag/documents", methods=["POST"])
@ai_admin_required
def ingest_rag_document():
    payload = request.get_json(silent=True) or {}
    ctx = _ctx()
    try:
        return AIRagService.ingest_document(
            organization_id=ctx.get("organization_id"),
            title=payload.get("title", ""),
            content=payload.get("content", ""),
            source_type=payload.get("source_type", "KNOWLEDGE"),
        ), 201
    except AIRagError as exc:
        return {"error": str(exc)}, 400


@ai_platform_bp.route("/rag/retrieve", methods=["POST"])
@ai_infer_required
def retrieve_rag():
    payload = request.get_json(silent=True) or {}
    ctx = _ctx()
    try:
        return AIRagService.retrieve(
            payload.get("query", ""),
            organization_id=ctx.get("organization_id"),
            limit=int(payload.get("limit", 5)),
        ), 200
    except AIRagError as exc:
        return {"error": str(exc)}, 400


@ai_platform_bp.route("/audit", methods=["GET"])
@ai_gateway_required()
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
@ai_gateway_required()
def usage_metrics():
    return AIUsageMetricsService.summary()


@ai_platform_bp.route("/sdk/manifest", methods=["GET"])
def sdk_manifest():
    return {
        "sdk_version": "3.0.0",
        "base_path": "/api/v1/ai-platform",
        "methods": {
            "infer": "POST /infer",
            "memory": "POST /memory/sessions",
            "rag_retrieve": "POST /rag/retrieve",
            "audit": "GET /audit",
        },
        "auth": "Bearer JWT + optional X-Organization-Id",
        "gateway_only": True,
    }, 200
