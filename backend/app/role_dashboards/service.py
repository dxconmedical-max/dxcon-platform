"""Aggregate operational metrics for role dashboards (no patient PII)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from flask import request, session
from sqlalchemy import func

from app.business_engine.statuses import (
    ORDER_IN_TRANSIT,
    ORDER_LAB_RECEIVED,
    ORDER_PAID,
    ORDER_PAYMENT_PENDING,
    ORDER_PENDING_REVIEW,
    ORDER_RELEASED,
    ORDER_SAMPLING,
    ORDER_TESTING,
    RESULT_PENDING_REVIEW,
    RESULT_RELEASED,
)
from app.extensions.db import db
from app.role_dashboards.security import ROLE_DASHBOARD_ROLES, SAFE_METRIC_KEYS


class RoleDashboardError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _today_start() -> datetime:
    return datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)


def _organization_id() -> str | None:
    try:
        from flask import has_request_context

        if not has_request_context():
            return None
        return (
            request.headers.get("X-Organization-ID")
            or request.args.get("organization_id")
            or session.get("organization_id")
            or session.get("active_organization_id")
        )
    except Exception:
        return None


def _safe_count(query_fn) -> int:
    try:
        return int(query_fn() or 0)
    except Exception:
        db.session.rollback()
        return 0


def _orders_today() -> int:
    from app.models.biz_order import BizOrder

    start = _today_start()
    return _safe_count(lambda: BizOrder.query.filter(BizOrder.created_at >= start).count())


def _pending_collection() -> int:
    from app.models.biz_order import BizCollection, BizOrder
    from app.business_engine.statuses import COLLECTION_ASSIGNED, COLLECTION_ACCEPTED

    desk = _safe_count(
        lambda: BizCollection.query.filter(
            BizCollection.status.in_((COLLECTION_ASSIGNED, COLLECTION_ACCEPTED))
        ).count()
    )
    paid = _safe_count(
        lambda: BizOrder.query.filter(BizOrder.status.in_((ORDER_PAID, ORDER_SAMPLING))).count()
    )
    return max(desk, paid)


def _lab_queue() -> int:
    from app.models.biz_order import BizOrder

    return _safe_count(
        lambda: BizOrder.query.filter(
            BizOrder.status.in_(
                (ORDER_IN_TRANSIT, ORDER_LAB_RECEIVED, ORDER_TESTING, ORDER_PENDING_REVIEW)
            )
        ).count()
    )


def _overdue_tests(*, sla_hours: int = 24) -> int:
    """Orders stuck in lab processing longer than SLA without release."""
    from app.models.biz_order import BizOrder

    cutoff = datetime.utcnow() - timedelta(hours=sla_hours)
    return _safe_count(
        lambda: BizOrder.query.filter(
            BizOrder.status.in_((ORDER_LAB_RECEIVED, ORDER_TESTING, ORDER_PENDING_REVIEW)),
            BizOrder.updated_at < cutoff,
        ).count()
    )


def _avg_tat_minutes() -> float | None:
    from app.models.biz_order import BizResult

    rows = []
    try:
        rows = (
            BizResult.query.filter(
                BizResult.status == RESULT_RELEASED,
                BizResult.released_at.isnot(None),
                BizResult.created_at.isnot(None),
            )
            .order_by(BizResult.released_at.desc())
            .limit(100)
            .all()
        )
    except Exception:
        db.session.rollback()
        return None
    if not rows:
        return None
    totals = []
    for row in rows:
        try:
            totals.append((row.released_at - row.created_at).total_seconds() / 60.0)
        except Exception:
            continue
    if not totals:
        return None
    return round(sum(totals) / len(totals), 1)


def _critical_results() -> int:
    from app.models.biz_order import BizResultItem
    from app.models.clinical_report import CriticalResultAlert

    flags = _safe_count(
        lambda: BizResultItem.query.filter(
            BizResultItem.flag.in_(("CRITICAL_LOW", "CRITICAL_HIGH", "CRITICAL"))
        ).count()
    )
    alerts = _safe_count(
        lambda: CriticalResultAlert.query.filter(
            CriticalResultAlert.status.in_(("new", "acknowledged", "escalated"))
        ).count()
    )
    return flags + alerts


def _completed_reports() -> int:
    from app.models.biz_order import BizResult
    from app.models.clinical_report import ClinicalReport

    released = _safe_count(
        lambda: BizResult.query.filter(
            BizResult.status == RESULT_RELEASED,
            func.date(BizResult.released_at) == datetime.utcnow().date(),
        ).count()
    )
    org_id = _organization_id()

    def clinical_count():
        q = ClinicalReport.query.filter(
            ClinicalReport.report_status.in_(("released", "approved")),
            ClinicalReport.released_at >= _today_start(),
        )
        if org_id:
            q = q.filter(
                db.or_(
                    ClinicalReport.organization_id == org_id,
                    ClinicalReport.organization_id.is_(None),
                )
            )
        return q.count()

    clinical = _safe_count(clinical_count)
    return max(released, clinical)


def _operational_alerts() -> int:
    """Failed imports + open critical + overdue as a single ops signal."""
    failed = 0
    try:
        from app.models.lab_lis import LISImportFailedRow

        failed = LISImportFailedRow.query.filter_by(status="failed").count()
    except Exception:
        db.session.rollback()
    return failed + _critical_results() + _overdue_tests()


def _pending_payment() -> int:
    from app.models.biz_order import BizOrder

    return _safe_count(lambda: BizOrder.query.filter_by(status=ORDER_PAYMENT_PENDING).count())


def _admin_metrics() -> dict[str, Any]:
    from app.models.audit_log import AuditLog
    from app.models.user import User

    tenants = 0
    try:
        from app.models.partner_foundation import PartnerOrganization

        tenants = _safe_count(lambda: PartnerOrganization.query.count())
    except Exception:
        db.session.rollback()
        try:
            from app.models.crm_organization import Organization

            tenants = _safe_count(lambda: Organization.query.count())
        except Exception:
            db.session.rollback()

    return {
        "orders_today": _orders_today(),
        "pending_collection": _pending_collection(),
        "lab_queue": _lab_queue(),
        "overdue_tests": _overdue_tests(),
        "avg_tat_minutes": _avg_tat_minutes(),
        "critical_results": _critical_results(),
        "completed_reports": _completed_reports(),
        "operational_alerts": _operational_alerts(),
        "users": _safe_count(lambda: User.query.count()),
        "tenants": tenants,
        "audit_events_today": _safe_count(
            lambda: AuditLog.query.filter(AuditLog.created_at >= _today_start()).count()
        ),
    }


def _reception_metrics() -> dict[str, Any]:
    from app.services.reception_service import get_kpis

    kpis = {}
    try:
        kpis = get_kpis() or {}
    except Exception:
        db.session.rollback()
    return {
        "orders_today": _orders_today(),
        "pending_collection": _pending_collection(),
        "pending_payment": max(_pending_payment(), int(kpis.get("pending_payment") or 0)),
        "lab_queue": _lab_queue(),
        "completed_reports": _completed_reports(),
        "operational_alerts": _operational_alerts(),
        "todays_patients": int(kpis.get("todays_patients") or 0),
        "waiting_queue": int(kpis.get("waiting_queue") or 0),
        "new_registrations": int(kpis.get("new_registrations") or 0),
    }


def _lab_metrics() -> dict[str, Any]:
    from app.lab_workspace.service import workspace_dashboard

    dash = {}
    try:
        dash = workspace_dashboard() or {}
    except Exception:
        db.session.rollback()
    kpis = dash.get("kpis") or {}
    return {
        "orders_today": _orders_today(),
        "pending_collection": _pending_collection(),
        "lab_queue": max(_lab_queue(), int(kpis.get("incoming") or 0) + int(kpis.get("testing") or 0)),
        "overdue_tests": _overdue_tests(),
        "avg_tat_minutes": _avg_tat_minutes(),
        "critical_results": max(_critical_results(), int(kpis.get("abnormal_results") or 0)),
        "completed_reports": max(_completed_reports(), int(kpis.get("released_today") or 0)),
        "operational_alerts": max(
            _operational_alerts(),
            int(kpis.get("failed_imports") or 0) + int(kpis.get("rejected") or 0),
        ),
        "incoming": int(kpis.get("incoming") or 0),
        "testing": int(kpis.get("testing") or 0),
        "pending_validation": int(kpis.get("pending_validation") or 0),
        "pending_review": int(kpis.get("pending_review") or 0),
        "released_today": int(kpis.get("released_today") or 0),
    }


def _collector_metrics(*, scoped_collector_id: str | None = None) -> dict[str, Any]:
    from app.sample_collection_workspace.service import list_production_queue, workspace_dashboard

    dash = {}
    try:
        dash = workspace_dashboard() or {}
    except Exception:
        db.session.rollback()
    kpis = dash.get("kpis") or {}

    if scoped_collector_id:
        try:
            scoped = list_production_queue(
                role="COLLECTOR",
                scoped_collector_id=scoped_collector_id,
                include_desk=False,
            )
            items = scoped.get("items") or []
            awaiting = sum(
                1
                for i in items
                if (i.get("status") or "").upper()
                in {"PENDING", "CHECKED_IN", "ASSIGNED", "ACCEPTED"}
            )
            transit = sum(1 for i in items if (i.get("status") or "").upper() == "IN_TRANSIT")
            arrived = sum(
                1 for i in items if (i.get("status") or "").upper() in {"RECEIVED", "DELIVERED"}
            )
            return {
                "orders_today": _orders_today(),
                "pending_collection": awaiting,
                "awaiting_collection": awaiting,
                "in_transit": transit,
                "arrived_at_lab": arrived,
                "lab_queue": _lab_queue(),
                "operational_alerts": int(kpis.get("rejected") or 0),
                "completed_reports": _completed_reports(),
                "scoped": True,
            }
        except Exception:
            db.session.rollback()

    return {
        "orders_today": _orders_today(),
        "pending_collection": max(
            _pending_collection(), int(kpis.get("awaiting_collection") or 0)
        ),
        "awaiting_collection": int(kpis.get("awaiting_collection") or 0),
        "in_transit": int(kpis.get("in_transit") or 0),
        "arrived_at_lab": int(kpis.get("arrived_at_lab") or 0),
        "lab_queue": _lab_queue(),
        "operational_alerts": int(kpis.get("rejected") or 0),
        "completed_reports": _completed_reports(),
        "scoped": False,
    }


def _doctor_metrics() -> dict[str, Any]:
    from app.models.biz_order import BizResult

    pending_review = _safe_count(
        lambda: BizResult.query.filter_by(status=RESULT_PENDING_REVIEW).count()
    )
    return {
        "orders_today": _orders_today(),
        "pending_review": pending_review,
        "pending_validation": pending_review,
        "critical_results": _critical_results(),
        "completed_reports": _completed_reports(),
        "overdue_tests": _overdue_tests(),
        "avg_tat_minutes": _avg_tat_minutes(),
        "lab_queue": _lab_queue(),
        "operational_alerts": _operational_alerts(),
    }


def _patient_metrics(*, patient_code: str | None = None) -> dict[str, Any]:
    """Patient portal aggregates — scoped when patient_code is known; else empty zeros."""
    if not patient_code:
        return {
            "results_available": 0,
            "appointments": 0,
            "home_visits": 0,
            "messages_unread": 0,
            "completed_reports": 0,
            "scoped": False,
            "empty": True,
        }

    from app.models.biz_order import BizOrder, BizResult
    from app.models.clinical_report import ClinicalReport

    orders = _safe_count(lambda: BizOrder.query.filter_by(patient_code=patient_code).count())
    released = _safe_count(
        lambda: BizResult.query.join(BizOrder, BizResult.order_id == BizOrder.id)
        .filter(BizOrder.patient_code == patient_code, BizResult.status == RESULT_RELEASED)
        .count()
    )
    reports = _safe_count(
        lambda: ClinicalReport.query.filter(
            ClinicalReport.patient_id == patient_code,
            ClinicalReport.report_status.in_(("released", "approved")),
            ClinicalReport.is_visible_to_patient.is_(True),
        ).count()
    )
    return {
        "results_available": max(released, reports),
        "appointments": orders,
        "home_visits": 0,
        "messages_unread": 0,
        "completed_reports": max(released, reports),
        "scoped": True,
        "empty": orders == 0 and released == 0,
    }


def _cards_for_role(role_key: str, metrics: dict[str, Any]) -> list[dict[str, str]]:
    """UI-ready status cards — values as strings, labels human-readable."""

    def fmt(key: str, label: str, hint: str | None = None) -> dict[str, str]:
        val = metrics.get(key)
        if val is None:
            display = "—"
        elif isinstance(val, float):
            display = f"{val:g}"
        else:
            display = str(val)
        card = {"label": label, "value": display}
        if hint:
            card["hint"] = hint
        return card

    mapping = {
        "admin": [
            fmt("orders_today", "Orders today"),
            fmt("pending_collection", "Pending collection"),
            fmt("lab_queue", "Lab queue"),
            fmt("operational_alerts", "Ops alerts", "Critical + overdue + failed imports"),
            fmt("critical_results", "Critical results"),
            fmt("completed_reports", "Completed reports"),
            fmt("avg_tat_minutes", "Avg TAT (min)"),
            fmt("overdue_tests", "Overdue tests"),
        ],
        "administration": None,
        "reception": [
            fmt("orders_today", "Orders today"),
            fmt("pending_payment", "Pending payment"),
            fmt("pending_collection", "Pending collection"),
            fmt("waiting_queue", "Waiting queue"),
        ],
        "laboratory": [
            fmt("incoming", "Incoming"),
            fmt("lab_queue", "Lab queue"),
            fmt("pending_validation", "Pending validation"),
            fmt("critical_results", "Critical / abnormal"),
            fmt("released_today", "Released today"),
            fmt("avg_tat_minutes", "Avg TAT (min)"),
            fmt("overdue_tests", "Overdue"),
            fmt("operational_alerts", "Alerts"),
        ],
        "lab": None,
        "collector": [
            fmt("awaiting_collection", "Awaiting collection"),
            fmt("in_transit", "In transit"),
            fmt("arrived_at_lab", "Arrived at lab"),
            fmt("operational_alerts", "Rejected / alerts"),
        ],
        "doctor": [
            fmt("pending_review", "Pending reviews"),
            fmt("critical_results", "Critical flags"),
            fmt("completed_reports", "Completed reports"),
            fmt("overdue_tests", "Overdue"),
        ],
        "patient": [
            fmt("results_available", "Results"),
            fmt("appointments", "Orders / visits"),
            fmt("home_visits", "Home visits"),
            fmt("messages_unread", "Messages"),
        ],
    }
    mapping["administration"] = mapping["admin"]
    mapping["lab"] = mapping["laboratory"]
    return mapping.get(role_key, mapping["admin"])


def build_role_dashboard(
    role_key: str,
    *,
    scoped_collector_id: str | None = None,
    patient_code: str | None = None,
) -> dict[str, Any]:
    key = (role_key or "").strip().lower()
    if key not in ROLE_DASHBOARD_ROLES:
        raise RoleDashboardError(f"Unknown dashboard role: {role_key}", 404)

    if key in {"admin", "administration"}:
        metrics = _admin_metrics()
    elif key == "reception":
        metrics = _reception_metrics()
    elif key in {"laboratory", "lab"}:
        metrics = _lab_metrics()
    elif key == "collector":
        metrics = _collector_metrics(scoped_collector_id=scoped_collector_id)
    elif key == "doctor":
        metrics = _doctor_metrics()
    elif key == "patient":
        metrics = _patient_metrics(patient_code=patient_code)
    else:
        metrics = _admin_metrics()

    # Strip anything that is not a safe aggregate key (defense in depth).
    clean = {k: v for k, v in metrics.items() if k in SAFE_METRIC_KEYS or k in {"scoped", "empty"}}
    cards = _cards_for_role(key, metrics)
    empty = bool(metrics.get("empty")) or all(
        (isinstance(c.get("value"), str) and c["value"] in {"0", "—", "0.0"}) for c in cards
    )

    return {
        "role": key,
        "organization_id": _organization_id(),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "metrics": clean,
        "cards": cards,
        "empty": empty and key == "patient",
        "pii_policy": "aggregates_only",
        "tenant_note": (
            "ClinicalReport respects X-Organization-ID when present; "
            "biz_orders lack organization_id (accepted limitation)."
        ),
    }


def role_can_access(actor_role: str | None, dashboard_key: str) -> bool:
    allowed = ROLE_DASHBOARD_ROLES.get((dashboard_key or "").lower(), frozenset())
    return bool(actor_role) and actor_role in allowed
