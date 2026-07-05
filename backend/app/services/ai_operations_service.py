"""AI operations business logic for Phase 5 Sprint 5.10."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from typing import Any

from app.ai_platform.metrics import AIUsageMetricsService
from app.ai_platform.models import AIInferenceJob, AIProvider, AIAuditLog, PromptTemplate, PromptVersion
from app.ai_platform.prompt_registry import PromptRegistry
from app.services.enterprise_analytics_service import ai_usage_analytics
from app.services.reporting_service import _date_range, _filter_created, _safe

AI_OPERATIONS_ROLES = ("SUPER_ADMIN", "ADMIN")

TOKEN_COST_PER_1K_IN = 0.0015
TOKEN_COST_PER_1K_OUT = 0.0020

FEATURES = (
    "AI Incident Summary",
    "AI Usage",
    "AI Cost",
    "AI Accuracy",
    "Model Health",
    "Prompt Version",
)


def ensure_ai_operations() -> dict[str, Any]:
    return {"ready": True, "read_only": True}


def _period(date_from=None, date_to=None) -> tuple[datetime, datetime]:
    return _date_range(date_from, date_to)


def ai_incident_summary(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_ai_operations()
    start, end = _period(date_from, date_to)
    failed_jobs = _safe(
        lambda: _filter_created(
            AIInferenceJob.query.filter(AIInferenceJob.status.in_(("FAILED", "ERROR", "CANCELLED"))),
            AIInferenceJob,
            start,
            end,
        )
        .order_by(AIInferenceJob.created_at.desc())
        .limit(25)
        .all(),
        [],
    )
    audit_errors = _safe(
        lambda: AIAuditLog.query.filter(
            AIAuditLog.created_at >= start,
            AIAuditLog.created_at <= end,
            AIAuditLog.action.in_(("inference.failed", "provider.error", "safety.blocked")),
        )
        .order_by(AIAuditLog.created_at.desc())
        .limit(25)
        .all(),
        [],
    )
    from app.models.incident import Incident

    ai_incidents = _safe(
        lambda: Incident.query.filter(
            Incident.created_at >= start,
            Incident.created_at <= end,
        )
        .filter(
            (Incident.incident_type.ilike("%ai%"))
            | (Incident.related_object_type.ilike("%ai%"))
            | (Incident.title.ilike("%ai%"))
        )
        .order_by(Incident.created_at.desc())
        .limit(25)
        .all(),
        [],
    )
    open_failures = len(failed_jobs)
    status = "OK" if open_failures == 0 and len(audit_errors) == 0 else "WARN"
    if open_failures >= 5:
        status = "CRITICAL"
    return {
        "report": "ai_incident_summary",
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "read_only": True,
        "status": status,
        "summary": {
            "failed_inference_jobs": open_failures,
            "audit_error_events": len(audit_errors),
            "ai_incidents": len(ai_incidents),
        },
        "failed_jobs": [row.to_dict() for row in failed_jobs],
        "audit_events": [row.to_dict() for row in audit_errors],
        "incidents": [row.to_dict() for row in ai_incidents],
    }


def ai_usage_metrics(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_ai_operations()
    payload = ai_usage_analytics(date_from, date_to)
    payload["report"] = "ai_usage_metrics"
    return payload


def ai_cost_metrics(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_ai_operations()
    start, end = _period(date_from, date_to)
    usage = AIUsageMetricsService.summary()
    totals = usage["totals"]
    tokens_in = totals.get("tokens_in", 0)
    tokens_out = totals.get("tokens_out", 0)
    cost_in = round((tokens_in / 1000) * TOKEN_COST_PER_1K_IN, 4)
    cost_out = round((tokens_out / 1000) * TOKEN_COST_PER_1K_OUT, 4)
    total_cost = round(cost_in + cost_out, 4)

    by_task: list[dict[str, Any]] = []
    for task_type, bucket in totals.get("by_task_type", {}).items():
        task_in = bucket.get("tokens_in", 0)
        task_out = bucket.get("tokens_out", 0)
        task_cost = round(
            (task_in / 1000) * TOKEN_COST_PER_1K_IN + (task_out / 1000) * TOKEN_COST_PER_1K_OUT,
            4,
        )
        by_task.append(
            {
                "task_type": task_type,
                "requests": bucket.get("requests", 0),
                "tokens_in": task_in,
                "tokens_out": task_out,
                "estimated_cost_usd": task_cost,
            }
        )
    by_task.sort(key=lambda row: row["estimated_cost_usd"], reverse=True)

    return {
        "report": "ai_cost_metrics",
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "read_only": True,
        "pricing": {
            "token_cost_per_1k_in": TOKEN_COST_PER_1K_IN,
            "token_cost_per_1k_out": TOKEN_COST_PER_1K_OUT,
            "currency": "USD",
            "note": "Advisory estimate for pilot budgeting.",
        },
        "totals": {
            "requests": totals.get("requests", 0),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "estimated_cost_usd": total_cost,
            "input_cost_usd": cost_in,
            "output_cost_usd": cost_out,
        },
        "by_task_type": by_task,
    }


def ai_accuracy_metrics(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_ai_operations()
    start, end = _period(date_from, date_to)
    jobs = _safe(
        lambda: _filter_created(AIInferenceJob.query, AIInferenceJob, start, end).all(),
        [],
    )
    status_counts = Counter(job.status for job in jobs)
    completed = status_counts.get("COMPLETED", 0)
    failed = sum(status_counts.get(status, 0) for status in ("FAILED", "ERROR", "CANCELLED"))
    total = len(jobs) or 1
    reviewed = sum(1 for job in jobs if job.human_review_required and job.status == "COMPLETED")
    success_rate = round((completed / total) * 100, 2)
    failure_rate = round((failed / total) * 100, 2)
    review_rate = round((reviewed / total) * 100, 2) if jobs else 0

    usage = ai_usage_analytics(date_from, date_to)
    return {
        "report": "ai_accuracy_metrics",
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "read_only": True,
        "jobs_total": len(jobs),
        "success_rate_percent": success_rate,
        "failure_rate_percent": failure_rate,
        "human_review_completion_percent": review_rate,
        "by_status": dict(status_counts),
        "interpretation_rate_percent": usage.get("interpretation_rate_percent", 0),
    }


def model_health_metrics(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_ai_operations()
    start, end = _period(date_from, date_to)
    providers = _safe(lambda: AIProvider.query.order_by(AIProvider.created_at.asc()).all(), [])
    jobs = _safe(
        lambda: _filter_created(AIInferenceJob.query, AIInferenceJob, start, end).all(),
        [],
    )
    jobs_by_provider = Counter(job.provider_id for job in jobs if job.provider_id)
    failures_by_provider = Counter(
        job.provider_id
        for job in jobs
        if job.provider_id and job.status in ("FAILED", "ERROR", "CANCELLED")
    )

    models: list[dict[str, Any]] = []
    degraded = 0
    for provider in providers:
        assigned = jobs_by_provider.get(provider.id, 0)
        failed = failures_by_provider.get(provider.id, 0)
        success_rate = round(((assigned - failed) / assigned) * 100, 2) if assigned else 100.0
        health = "HEALTHY"
        if provider.status != "ACTIVE":
            health = "INACTIVE"
            degraded += 1
        elif assigned and success_rate < 90:
            health = "DEGRADED"
            degraded += 1
        models.append(
            {
                "provider_id": provider.id,
                "provider_code": provider.provider_code,
                "name": provider.name,
                "model_name": provider.model_name,
                "provider_type": provider.provider_type,
                "status": provider.status,
                "health": health,
                "jobs_in_period": assigned,
                "failures_in_period": failed,
                "success_rate_percent": success_rate,
            }
        )

    platform_status = "OK" if degraded == 0 else "DEGRADED"
    return {
        "report": "model_health_metrics",
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "read_only": True,
        "platform_status": platform_status,
        "providers_total": len(models),
        "providers_degraded": degraded,
        "models": models,
    }


def prompt_version_metrics() -> dict[str, Any]:
    ensure_ai_operations()
    PromptRegistry.ensure_defaults()
    prompts = PromptRegistry.list_prompts()
    versions: list[dict[str, Any]] = []
    for prompt in prompts.get("prompts", []):
        version_rows = _safe(
            lambda pid=prompt["id"]: PromptVersion.query.filter_by(prompt_id=pid)
            .order_by(PromptVersion.version.desc())
            .all(),
            [],
        )
        active_version = prompt.get("active_version", 1)
        active_row = next((row for row in version_rows if row.version == active_version), None)
        metadata = {}
        if active_row and active_row.metadata_json:
            try:
                metadata = json.loads(active_row.metadata_json)
            except Exception:
                metadata = {}
        versions.append(
            {
                "prompt_id": prompt["id"],
                "prompt_code": prompt["prompt_code"],
                "name": prompt["name"],
                "task_type": prompt["task_type"],
                "active_version": active_version,
                "versions_total": len(version_rows),
                "active_template_preview": (active_row.template_text[:120] + "…")
                if active_row and len(active_row.template_text) > 120
                else (active_row.template_text if active_row else ""),
                "metadata": metadata,
            }
        )

    return {
        "report": "prompt_version_metrics",
        "read_only": True,
        "prompts_total": prompts.get("count", 0),
        "prompts": versions,
        "registry_api": "/api/v1/ai-platform/prompts",
    }


def ai_operations_dashboard() -> dict[str, Any]:
    ensure_ai_operations()
    incidents = ai_incident_summary()
    usage = ai_usage_metrics()
    cost = ai_cost_metrics()
    accuracy = ai_accuracy_metrics()
    health = model_health_metrics()
    prompts = prompt_version_metrics()
    status = incidents["status"]
    if health["platform_status"] != "OK":
        status = "DEGRADED" if status == "OK" else status
    return {
        "report": "ai_operations_dashboard",
        "read_only": True,
        "status": status,
        "ai_requests": usage["usage"]["totals"]["requests"],
        "estimated_cost_usd": cost["totals"]["estimated_cost_usd"],
        "success_rate_percent": accuracy["success_rate_percent"],
        "providers_degraded": health["providers_degraded"],
        "prompts_total": prompts["prompts_total"],
        "failed_inference_jobs": incidents["summary"]["failed_inference_jobs"],
    }


def ai_operations_readiness_report() -> dict[str, Any]:
    dashboard = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "5.10",
        "sprint": "AI Operations",
        "platform": dashboard["platform"],
        "status": dashboard["status"],
        "summary": dashboard["summary"],
        "features": list(FEATURES),
        "sections": {
            "incident_summary": ai_incident_summary(),
            "usage": ai_usage_metrics(),
            "cost": ai_cost_metrics(),
            "accuracy": ai_accuracy_metrics(),
            "model_health": model_health_metrics(),
            "prompt_version": prompt_version_metrics(),
        },
        "legacy_routes": [
            "/api/v1/ai-platform/usage",
            "/api/v1/ai-platform/prompts",
            "/enterprise-analytics/ai",
        ],
    }


def dashboard_payload(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_ai_operations()
    dash = ai_operations_dashboard()
    return {
        "platform": "AI Operations",
        "phase": "5.10",
        "sprint": "AI Operations",
        "status": dash["status"],
        "read_only": True,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "ai_requests": dash["ai_requests"],
            "estimated_cost_usd": dash["estimated_cost_usd"],
            "success_rate_percent": dash["success_rate_percent"],
            "providers_degraded": dash["providers_degraded"],
            "prompts_total": dash["prompts_total"],
            "failed_inference_jobs": dash["failed_inference_jobs"],
        },
        "features": list(FEATURES),
    }
