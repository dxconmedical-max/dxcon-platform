"""Production worker and scheduler loops over existing job/queue services."""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime

logger = logging.getLogger("dxcon.process_runtime")


def _poll_seconds(role: str) -> float:
    key = f"DXCON_{role.upper()}_POLL_SECONDS"
    return float(os.getenv(key, os.getenv("DXCON_RUNTIME_POLL_SECONDS", "5")))


def cron_matches(expr: str, dt: datetime) -> bool:
    """Match a 5-field cron expression against a datetime (UTC/naive local)."""
    if not expr or not str(expr).strip():
        return False
    fields = str(expr).strip().split()
    if len(fields) != 5:
        return False
    minute, hour, day, month, weekday = fields
    cron_weekday = (dt.weekday() + 1) % 7  # 0=Sunday
    return (
        _cron_field_matches(minute, dt.minute, 0, 59)
        and _cron_field_matches(hour, dt.hour, 0, 23)
        and _cron_field_matches(day, dt.day, 1, 31)
        and _cron_field_matches(month, dt.month, 1, 12)
        and _cron_field_matches(weekday, cron_weekday, 0, 6)
    )


def _cron_field_matches(field: str, value: int, minimum: int, maximum: int) -> bool:
    field = field.strip()
    if field == "*":
        return True
    for part in field.split(","):
        part = part.strip()
        if part.startswith("*/"):
            step = int(part[2:])
            if step <= 0:
                return False
            if value % step == 0:
                return True
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start, end = int(start_s), int(end_s)
            if start <= value <= end:
                return True
            continue
        if int(part) == value:
            return True
    return False


def _require_runtime_dependencies(app):
    from app.infrastructure.production_readiness import (
        check_redis_health,
        is_production,
        validate_database,
        validate_queue_provider,
        validate_redis,
    )

    validate_queue_provider(app)
    if is_production(app):
        validate_database(app)
        validate_redis(app)
        health = check_redis_health(app)
        if not health.get("ok"):
            detail = health.get("error") or health.get("mode") or "unavailable"
            raise RuntimeError(f"Redis unavailable for production runtime: {detail}")
        from app.infrastructure.queue_provider import get_queue

        get_queue(app).ping()


def _dispatch_queue_item(item: dict):
    kind = str(item.get("type") or item.get("kind") or "noop").lower()
    if kind in {"noop", "heartbeat"}:
        return {"ok": True, "type": kind}
    if kind in {"scheduled", "scheduler"}:
        from app.models.operations_platform import ScheduledJob
        from app.operations.job_runner import JobRunner

        job = ScheduledJob.query.filter_by(id=item.get("job_id")).first()
        if job is None:
            raise ValueError("scheduled job not found")
        return JobRunner.run_job(job)
    if kind in {"integration", "integration_job"}:
        from app.services.integration_platform_service import IntegrationQueueService

        return IntegrationQueueService.process_job(item["job_id"])
    if kind in {"notification", "notifications"}:
        from app.services.communication_hub_service import QueueHubService

        return QueueHubService.process_queue(limit=int(item.get("limit") or 10))
    raise ValueError(f"unknown queue job type: {kind}")


def _drain_broker(app, limit: int) -> dict:
    from app.infrastructure.queue_provider import get_queue

    processed = 0
    errors = 0
    requeued = 0
    queue = get_queue(app)
    for _ in range(limit):
        claimed = queue.claim(timeout=0)
        if claimed is None:
            break
        item, claim_token = claimed
        try:
            _dispatch_queue_item(item)
            queue.ack(claim_token)
            processed += 1
        except Exception as exc:
            errors += 1
            logger.exception("queue item failed: %s", exc)
            if queue.nack(claim_token, requeue=True):
                requeued += 1
    return {"processed": processed, "errors": errors, "requeued": requeued}


def _drain_notifications(limit: int) -> dict:
    from app.services.communication_hub_service import QueueHubService

    try:
        result = QueueHubService.process_queue(limit=limit)
        return {"ok": True, "result": result}
    except Exception as exc:
        logger.exception("notification queue drain failed: %s", exc)
        return {"ok": False, "error": str(exc)}


def _drain_integrations(limit: int) -> dict:
    from app.core.statuses import INTEGRATION_JOB_FAILED, INTEGRATION_JOB_PENDING
    from app.models.integration_platform import IntegrationJob
    from app.services.integration_platform_service import IntegrationQueueService

    rows = (
        IntegrationJob.query.filter(
            IntegrationJob.status.in_((INTEGRATION_JOB_PENDING, INTEGRATION_JOB_FAILED))
        )
        .order_by(IntegrationJob.created_at.asc())
        .limit(limit)
        .all()
    )
    processed = 0
    errors = 0
    for row in rows:
        try:
            IntegrationQueueService.process_job(row.id)
            processed += 1
        except Exception as exc:
            errors += 1
            logger.exception("integration job %s failed: %s", row.id, exc)
    return {"processed": processed, "errors": errors, "candidates": len(rows)}


def run_worker_cycle(app, *, drain_limit=10) -> dict:
    _require_runtime_dependencies(app)
    broker = _drain_broker(app, drain_limit)
    notifications = _drain_notifications(drain_limit)
    integrations = _drain_integrations(drain_limit)
    return {
        "role": "worker",
        "broker": broker,
        "notifications": notifications,
        "integrations": integrations,
        "processed": broker["processed"] + integrations.get("processed", 0),
        "errors": broker["errors"] + integrations.get("errors", 0),
    }


def _ran_in_current_minute(job, now: datetime) -> bool:
    from app.models.operations_platform import ScheduledJobRun

    run = (
        ScheduledJobRun.query.filter_by(job_id=job.id)
        .order_by(ScheduledJobRun.started_at.desc())
        .first()
    )
    if run is None or run.started_at is None:
        return False
    started = run.started_at
    return started.replace(second=0, microsecond=0) == now.replace(second=0, microsecond=0)


def _tick_key(job_id, now: datetime) -> str:
    return f"{job_id}:{now.strftime('%Y%m%d%H%M')}"


def _already_scheduled_this_minute(app, job, now: datetime) -> bool:
    ticks = app.extensions.setdefault("dxcon_scheduler_ticks", set())
    if _tick_key(job.id, now) in ticks:
        return True
    return _ran_in_current_minute(job, now)


def run_scheduler_cycle(app, *, now=None) -> dict:
    from app.models.operations_platform import ScheduledJob
    from app.operations.job_runner import JobRunner
    from app.operations.scheduler_service import SchedulerService

    _require_runtime_dependencies(app)
    SchedulerService.ensure_defaults()
    now = now or datetime.utcnow()
    due = []
    errors = 0

    # Resume orphaned RETRY rows before cron firing so the same job is not
    # double-started (new run + leftover RETRY) in one cycle.
    retry_result = {"retried": 0, "errors": 0, "candidates": 0}
    try:
        retry_result = JobRunner.process_pending_retries(limit=20)
        errors += int(retry_result.get("errors") or 0)
    except Exception as exc:
        errors += 1
        logger.exception("pending retry processing failed: %s", exc)

    rows = ScheduledJob.query.filter_by(status="ENABLED").all()
    ticks = app.extensions.setdefault("dxcon_scheduler_ticks", set())
    for job in rows:
        if not cron_matches(job.cron_expression or "", now):
            continue
        if _already_scheduled_this_minute(app, job, now):
            continue
        try:
            JobRunner.run_job(job)
            ticks.add(_tick_key(job.id, now))
            due.append(job.job_code)
        except Exception as exc:
            errors += 1
            logger.exception("scheduled job %s failed: %s", job.job_code, exc)

    return {
        "role": "scheduler",
        "due": due,
        "checked": len(rows),
        "errors": errors,
        "retries": retry_result,
        "now": now.isoformat(),
    }


def run_worker_loop(app):
    poll = _poll_seconds("worker")
    with app.app_context():
        _require_runtime_dependencies(app)
        from app.infrastructure.queue_provider import get_queue

        queue = get_queue(app)
        recovered = queue.recover_inflight()
        if recovered:
            logger.warning("recovered %s orphaned in-flight queue job(s)", recovered)
        logger.info("dxcon worker started")
        while True:
            run_worker_cycle(app)
            time.sleep(poll)


def run_scheduler_loop(app):
    poll = _poll_seconds("scheduler")
    with app.app_context():
        _require_runtime_dependencies(app)
        logger.info("dxcon scheduler started")
        while True:
            run_scheduler_cycle(app)
            time.sleep(poll)
