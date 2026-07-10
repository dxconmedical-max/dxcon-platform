"""Operations Center service — Release 1.0 Operations Excellence.

Aggregates operational signals (incidents, support tickets, system health,
deployments, failed jobs, critical alerts, customer requests) for the
Operations Center dashboard. Read-only aggregation plus lightweight
create/update flows for support tickets and customer requests.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from app.core.deployment import deployment_readiness
from app.extensions.db import db
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.operations_center import CustomerRequest, SupportTicket
from app.models.operations_platform import DeploymentRecord, ScheduledJobRun
from app.operations_center.audit import write_ops_center_audit

OPEN_INCIDENT_STATUSES = ("OPEN", "INVESTIGATING", "IN_PROGRESS")
OPEN_TICKET_STATUSES = ("OPEN", "IN_PROGRESS", "WAITING")
PENDING_REQUEST_STATUSES = ("PENDING", "REVIEW", "IN_PROGRESS")
FAILED_JOB_STATUSES = ("FAILED", "ERROR")


class OpsCenterError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.utcnow()


def _safe_count(query_fn) -> int:
    try:
        return int(query_fn() or 0)
    except SQLAlchemyError:
        db.session.rollback()
        return 0


def _safe_list(query_fn) -> list:
    try:
        return list(query_fn() or [])
    except SQLAlchemyError:
        db.session.rollback()
        return []


def _system_health() -> dict[str, Any]:
    try:
        report = deployment_readiness(current_app._get_current_object())
        score = report.get("score", 0)
        status = "OK" if score >= 80 else "DEGRADED" if score >= 50 else "CRITICAL"
        return {"status": status, "score": score, "ready": report.get("ready_for_production", False)}
    except Exception:
        return {"status": "UNKNOWN", "score": 0, "ready": False}


def dashboard() -> dict[str, Any]:
    """Operations Center dashboard with the seven operational widgets."""
    open_incidents = _safe_count(
        lambda: Incident.query.filter(Incident.status.in_(OPEN_INCIDENT_STATUSES)).count()
    )
    open_tickets = _safe_count(
        lambda: SupportTicket.query.filter(SupportTicket.status.in_(OPEN_TICKET_STATUSES)).count()
    )
    health = _system_health()
    deployments = _safe_count(lambda: DeploymentRecord.query.count())
    failed_jobs = _safe_count(
        lambda: ScheduledJobRun.query.filter(ScheduledJobRun.status.in_(FAILED_JOB_STATUSES)).count()
    )
    critical_alerts = _safe_count(
        lambda: Alert.query.filter(
            Alert.severity.in_(("CRITICAL", "HIGH")), Alert.status == "OPEN"
        ).count()
    )
    pending_requests = _safe_count(
        lambda: CustomerRequest.query.filter(
            CustomerRequest.status.in_(PENDING_REQUEST_STATUSES)
        ).count()
    )

    widgets = {
        "open_incidents": open_incidents,
        "open_support_tickets": open_tickets,
        "system_health": health["status"],
        "system_health_score": health["score"],
        "deployments": deployments,
        "failed_jobs": failed_jobs,
        "critical_alerts": critical_alerts,
        "pending_customer_requests": pending_requests,
    }

    return {
        "generated_at": _utcnow().isoformat(),
        "widgets": widgets,
        "recent_incidents": [
            i.to_dict()
            for i in _safe_list(
                lambda: Incident.query.filter(Incident.status.in_(OPEN_INCIDENT_STATUSES))
                .order_by(Incident.created_at.desc())
                .limit(8)
                .all()
            )
        ],
        "recent_tickets": [
            t.to_dict()
            for t in _safe_list(
                lambda: SupportTicket.query.filter(SupportTicket.status.in_(OPEN_TICKET_STATUSES))
                .order_by(SupportTicket.created_at.desc())
                .limit(8)
                .all()
            )
        ],
        "recent_deployments": [
            d.to_dict()
            for d in _safe_list(
                lambda: DeploymentRecord.query.order_by(DeploymentRecord.created_at.desc())
                .limit(5)
                .all()
            )
        ],
        "recent_failed_jobs": [
            j.to_dict()
            for j in _safe_list(
                lambda: ScheduledJobRun.query.filter(ScheduledJobRun.status.in_(FAILED_JOB_STATUSES))
                .order_by(ScheduledJobRun.started_at.desc())
                .limit(8)
                .all()
            )
        ],
        "recent_alerts": [
            a.to_dict()
            for a in _safe_list(
                lambda: Alert.query.filter(
                    Alert.severity.in_(("CRITICAL", "HIGH")), Alert.status == "OPEN"
                )
                .order_by(Alert.created_at.desc())
                .limit(8)
                .all()
            )
        ],
        "pending_requests": [
            r.to_dict()
            for r in _safe_list(
                lambda: CustomerRequest.query.filter(
                    CustomerRequest.status.in_(PENDING_REQUEST_STATUSES)
                )
                .order_by(CustomerRequest.created_at.desc())
                .limit(8)
                .all()
            )
        ],
    }


def list_support_tickets(*, status: str | None = None, limit: int = 100) -> dict[str, Any]:
    q = SupportTicket.query
    if status:
        q = q.filter(SupportTicket.status == status)
    rows = _safe_list(lambda: q.order_by(SupportTicket.created_at.desc()).limit(limit).all())
    return {"count": len(rows), "data": [r.to_dict() for r in rows]}


def create_support_ticket(data: dict, *, actor: str | None = None) -> dict[str, Any]:
    data = data or {}
    subject = (data.get("subject") or "").strip()
    if not subject:
        raise OpsCenterError("subject is required")
    ticket = SupportTicket(
        ticket_code=data.get("ticket_code") or f"TKT-{uuid.uuid4().hex[:8].upper()}",
        organization_id=data.get("organization_id"),
        subject=subject,
        description=data.get("description"),
        category=data.get("category") or "GENERAL",
        priority=data.get("priority") or "NORMAL",
        status="OPEN",
        requester_email=data.get("requester_email") or actor,
        assigned_to=data.get("assigned_to"),
    )
    db.session.add(ticket)
    db.session.flush()
    write_ops_center_audit(
        action="support_ticket_created",
        object_type="support_ticket",
        object_id=ticket.ticket_code,
        actor=actor,
    )
    return ticket.to_dict()


def update_support_ticket_status(ticket_code: str, status: str, *, actor: str | None = None) -> dict[str, Any]:
    ticket = SupportTicket.query.filter_by(ticket_code=ticket_code).first()
    if not ticket:
        raise OpsCenterError("Support ticket not found")
    ticket.status = status
    if status in ("RESOLVED", "CLOSED"):
        ticket.resolved_at = _utcnow()
    write_ops_center_audit(
        action="support_ticket_status_changed",
        object_type="support_ticket",
        object_id=ticket.ticket_code,
        actor=actor,
    )
    return ticket.to_dict()


def list_customer_requests(*, status: str | None = None, limit: int = 100) -> dict[str, Any]:
    q = CustomerRequest.query
    if status:
        q = q.filter(CustomerRequest.status == status)
    rows = _safe_list(lambda: q.order_by(CustomerRequest.created_at.desc()).limit(limit).all())
    return {"count": len(rows), "data": [r.to_dict() for r in rows]}


def create_customer_request(data: dict, *, actor: str | None = None) -> dict[str, Any]:
    data = data or {}
    title = (data.get("title") or "").strip()
    if not title:
        raise OpsCenterError("title is required")
    request_row = CustomerRequest(
        request_code=data.get("request_code") or f"REQ-{uuid.uuid4().hex[:8].upper()}",
        organization_id=data.get("organization_id"),
        request_type=data.get("request_type") or "FEATURE",
        title=title,
        details=data.get("details"),
        status="PENDING",
        priority=data.get("priority") or "NORMAL",
        requested_by=data.get("requested_by") or actor,
    )
    db.session.add(request_row)
    db.session.flush()
    write_ops_center_audit(
        action="customer_request_created",
        object_type="customer_request",
        object_id=request_row.request_code,
        actor=actor,
    )
    return request_row.to_dict()


def update_customer_request_status(request_code: str, status: str, *, actor: str | None = None) -> dict[str, Any]:
    request_row = CustomerRequest.query.filter_by(request_code=request_code).first()
    if not request_row:
        raise OpsCenterError("Customer request not found")
    request_row.status = status
    if status in ("RESOLVED", "CLOSED", "DELIVERED"):
        request_row.resolved_at = _utcnow()
    write_ops_center_audit(
        action="customer_request_status_changed",
        object_type="customer_request",
        object_id=request_row.request_code,
        actor=actor,
    )
    return request_row.to_dict()


def operations_center_report() -> dict[str, Any]:
    data = dashboard()
    return {
        "report": "operations_center",
        "release": "1.0-operations-excellence",
        "generated_at": data["generated_at"],
        "widgets": data["widgets"],
    }
