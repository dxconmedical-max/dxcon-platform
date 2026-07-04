"""Pilot operations status business logic for Phase 5 Sprint 5.6."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.infrastructure.schema_introspection import table_exists_name
from app.web.demo_pilot_lib import safe_query, system_status
from app.web.pilot_dashboard_data import executive_metrics

PILOT_STATUS_ROLES = ("SUPER_ADMIN", "ADMIN")

FEATURES = (
    "Pilot Status",
    "Active Clinics",
    "Active Labs",
    "Collectors Online",
    "Doctors Online",
    "Today's Orders",
    "Today's Revenue",
    "Alerts",
)


class PilotStatusError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def ensure_pilot_status() -> dict[str, Any]:
    return {"ready": True, "read_only": True}


def _today_start() -> datetime:
    return datetime.combine(date.today(), datetime.min.time())


def _snapshot() -> dict[str, Any]:
    from app.models.alert import Alert
    from app.models.clinic_profile import ClinicProfile
    from app.models.doctor_profile import DoctorProfile
    from app.models.driver import Driver
    from app.models.laboratory import Laboratory
    from app.models.order import Order
    from app.models.payment import Payment
    from app.models.user import User

    clinics = []
    if table_exists_name("clinic_profiles"):
        clinics = [
            row.to_dict()
            for row in ClinicProfile.query.filter(ClinicProfile.status == "ACTIVE").all()
        ]

    labs = []
    if table_exists_name("laboratories"):
        labs = [
            row.to_dict()
            for row in Laboratory.query.filter_by(is_active=True).all()
        ]

    collectors = safe_query(Driver, limit=100)
    collectors_online = [
        row.to_dict()
        for row in collectors
        if (row.status or "").upper() == "ACTIVE" or (row.ops_status or "").upper() == "ACTIVE"
    ]

    doctors = []
    if table_exists_name("doctor_profiles"):
        doctors = [row.to_dict() for row in safe_query(DoctorProfile, limit=100)]
    doctor_users = User.query.filter(User.role == "DOCTOR", User.is_active.is_(True)).count()

    today = _today_start()
    orders_today = []
    if table_exists_name("orders"):
        orders_today = [
            row.to_dict()
            for row in Order.query.filter(Order.created_at >= today).order_by(Order.created_at.desc()).limit(50).all()
        ]

    revenue_today = 0.0
    if table_exists_name("payments"):
        revenue_today = sum(
            (payment.amount or 0)
            for payment in Payment.query.filter(Payment.created_at >= today).all()
        )
    if revenue_today == 0 and orders_today:
        revenue_today = sum((order.get("total_amount") or 0) for order in orders_today)

    metrics = executive_metrics()
    if not orders_today and metrics.get("today_orders"):
        revenue_today = revenue_today or metrics.get("today_revenue", 0)

    alerts_open = []
    if table_exists_name("alerts"):
        alerts_open = [
            row.to_dict()
            for row in Alert.query.filter_by(status="OPEN").order_by(Alert.created_at.desc()).limit(25).all()
        ]

    return {
        "active_clinics": len(clinics),
        "active_labs": len(labs),
        "collectors_online": len(collectors_online),
        "doctors_online": max(len(doctors), doctor_users),
        "todays_orders": len(orders_today) or metrics.get("today_orders", 0),
        "todays_revenue": revenue_today or metrics.get("today_revenue", 0),
        "alerts_open": len(alerts_open),
        "clinics": clinics[:10],
        "labs": labs[:10],
        "collectors": collectors_online[:10],
        "doctors": doctors[:10],
        "orders": orders_today[:10],
        "alerts": alerts_open[:10],
        "system": system_status(),
    }


def pilot_status_overview() -> dict[str, Any]:
    ensure_pilot_status()
    snap = _snapshot()
    system = snap["system"]
    status = "OK"
    if system.get("status") not in {"OK", "DEGRADED"}:
        status = "WARN"
    if snap["alerts_open"] > 10:
        status = "WARN"
    return {
        "report": "pilot_status",
        "read_only": True,
        "status": status,
        "architecture": (
            "Pilot Status → Active Clinics → Active Labs → Collectors Online → "
            "Doctors Online → Today's Orders → Today's Revenue → Alerts"
        ),
        "summary": {
            "active_clinics": snap["active_clinics"],
            "active_labs": snap["active_labs"],
            "collectors_online": snap["collectors_online"],
            "doctors_online": snap["doctors_online"],
            "todays_orders": snap["todays_orders"],
            "todays_revenue": snap["todays_revenue"],
            "alerts_open": snap["alerts_open"],
        },
        "system": system,
        "legacy_routes": ["/executive-v9", "/pilot-checklist", "/api/v1/dashboard/summary"],
    }


def active_clinics() -> dict[str, Any]:
    ensure_pilot_status()
    snap = _snapshot()
    return {
        "report": "active_clinics",
        "read_only": True,
        "count": snap["active_clinics"],
        "clinics": snap["clinics"],
    }


def active_labs() -> dict[str, Any]:
    ensure_pilot_status()
    snap = _snapshot()
    return {
        "report": "active_labs",
        "read_only": True,
        "count": snap["active_labs"],
        "labs": snap["labs"],
    }


def collectors_online() -> dict[str, Any]:
    ensure_pilot_status()
    snap = _snapshot()
    return {
        "report": "collectors_online",
        "read_only": True,
        "count": snap["collectors_online"],
        "collectors": snap["collectors"],
    }


def doctors_online() -> dict[str, Any]:
    ensure_pilot_status()
    snap = _snapshot()
    return {
        "report": "doctors_online",
        "read_only": True,
        "count": snap["doctors_online"],
        "doctors": snap["doctors"],
    }


def todays_orders() -> dict[str, Any]:
    ensure_pilot_status()
    snap = _snapshot()
    return {
        "report": "todays_orders",
        "read_only": True,
        "count": snap["todays_orders"],
        "orders": snap["orders"],
    }


def todays_revenue() -> dict[str, Any]:
    ensure_pilot_status()
    snap = _snapshot()
    metrics = executive_metrics()
    return {
        "report": "todays_revenue",
        "read_only": True,
        "amount": snap["todays_revenue"],
        "currency": "VND",
        "executive_metrics": {
            "today_revenue": metrics.get("today_revenue", 0),
            "today_orders": metrics.get("today_orders", 0),
        },
    }


def pilot_alerts() -> dict[str, Any]:
    ensure_pilot_status()
    snap = _snapshot()
    severity_counts: dict[str, int] = {}
    for alert in snap["alerts"]:
        severity = (alert.get("severity") or "MEDIUM").upper()
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    return {
        "report": "alerts",
        "read_only": True,
        "open_count": snap["alerts_open"],
        "severity_counts": severity_counts,
        "alerts": snap["alerts"],
        "legacy_route": "/alerts",
    }


def pilot_status_dashboard() -> dict[str, Any]:
    overview = pilot_status_overview()
    return {
        "report": "pilot_status_dashboard",
        "read_only": True,
        "status": overview["status"],
        **overview["summary"],
    }


def pilot_status_readiness_report() -> dict[str, Any]:
    dashboard = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "5.6",
        "sprint": "Pilot Status",
        "platform": dashboard["platform"],
        "status": dashboard["status"],
        "summary": dashboard["summary"],
        "features": list(FEATURES),
        "sections": {
            "pilot_status": pilot_status_overview(),
            "active_clinics": active_clinics(),
            "active_labs": active_labs(),
            "collectors_online": collectors_online(),
            "doctors_online": doctors_online(),
            "todays_orders": todays_orders(),
            "todays_revenue": todays_revenue(),
            "alerts": pilot_alerts(),
        },
    }


def dashboard_payload() -> dict[str, Any]:
    ensure_pilot_status()
    overview = pilot_status_overview()
    summary = overview["summary"]
    return {
        "platform": "Pilot Status",
        "phase": "5.6",
        "sprint": "Pilot Status",
        "status": overview["status"],
        "read_only": True,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": summary,
        "features": list(FEATURES),
    }
