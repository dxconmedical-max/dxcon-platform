"""Executive metrics business logic for Phase 5 Sprint 5.9."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from app.core.statuses import BILLING_INVOICE_PAID
from app.models.clinic_profile import ClinicProfile
from app.models.clinic_referral import ClinicReferral
from app.models.doctor_profile import DoctorProfile
from app.models.invoice import Invoice
from app.models.medical_order import MedicalOrder
from app.models.test_result import TestResult
from app.services.crm_dashboard_service import CrmDashboardService
from app.services.enterprise_analytics_service import (
    collector_sla_analytics,
    lab_sla_analytics,
    revenue_analytics,
    turnaround_time_analytics,
)
from app.services.reporting_service import ReportingService, _date_range, _filter_created, _safe

EXECUTIVE_METRICS_ROLES = ("SUPER_ADMIN", "ADMIN")

FEATURES = (
    "Revenue",
    "TAT",
    "Orders",
    "Growth",
    "Lab SLA",
    "Collector SLA",
    "Clinic Ranking",
    "Doctor Ranking",
    "Revenue Forecast",
)


def ensure_executive_metrics() -> dict[str, Any]:
    return {"ready": True, "read_only": True}


def _period(date_from=None, date_to=None) -> tuple[datetime, datetime]:
    return _date_range(date_from, date_to)


def _pct_change(current: float, previous: float) -> float:
    if previous:
        return round(((current - previous) / previous) * 100, 2)
    return 100.0 if current else 0.0


def revenue_metrics(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_executive_metrics()
    payload = revenue_analytics(date_from, date_to)
    payload["report"] = "revenue_metrics"
    return payload


def tat_metrics(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_executive_metrics()
    payload = turnaround_time_analytics(date_from, date_to)
    payload["report"] = "tat_metrics"
    return payload


def orders_metrics(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_executive_metrics()
    distribution = ReportingService.order_status_distribution(date_from, date_to)
    start, end = _period(date_from, date_to)
    completed = _safe(
        lambda: _filter_created(
            MedicalOrder.query.filter(MedicalOrder.status.in_(("COMPLETED", "COLLECTED", "IN_LAB"))),
            MedicalOrder,
            start,
            end,
        ).count()
    )
    pending = _safe(
        lambda: _filter_created(
            MedicalOrder.query.filter(MedicalOrder.status.in_(("BOOKED", "PENDING", "ASSIGNED"))),
            MedicalOrder,
            start,
            end,
        ).count()
    )
    return {
        "report": "orders_metrics",
        "period_start": distribution["period_start"],
        "period_end": distribution["period_end"],
        "read_only": True,
        "orders_total": distribution.get("total", 0),
        "completed_orders": completed,
        "pending_orders": pending,
        "by_status": distribution.get("by_status", {}),
    }


def growth_metrics(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_executive_metrics()
    start, end = _period(date_from, date_to)
    span_days = max((end - start).days, 1)
    previous_end = start - timedelta(seconds=1)
    previous_start = previous_end - timedelta(days=span_days)

    current_revenue = revenue_analytics(start, end)
    previous_revenue = revenue_analytics(previous_start, previous_end)
    current_orders = orders_metrics(start, end)
    previous_orders = orders_metrics(previous_start, previous_end)

    current_gross = float(current_revenue.get("gross_revenue", 0) or 0)
    previous_gross = float(previous_revenue.get("gross_revenue", 0) or 0)
    current_total = int(current_orders.get("orders_total", 0) or 0)
    previous_total = int(previous_orders.get("orders_total", 0) or 0)

    return {
        "report": "growth_metrics",
        "read_only": True,
        "current_period": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "gross_revenue": current_gross,
            "orders_total": current_total,
        },
        "previous_period": {
            "start": previous_start.isoformat(),
            "end": previous_end.isoformat(),
            "gross_revenue": previous_gross,
            "orders_total": previous_total,
        },
        "growth": {
            "revenue_percent": _pct_change(current_gross, previous_gross),
            "orders_percent": _pct_change(float(current_total), float(previous_total)),
            "revenue_delta": round(current_gross - previous_gross, 2),
            "orders_delta": current_total - previous_total,
        },
    }


def lab_sla_metrics(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_executive_metrics()
    payload = lab_sla_analytics(date_from, date_to)
    payload["report"] = "lab_sla_metrics"
    return payload


def collector_sla_metrics(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_executive_metrics()
    payload = collector_sla_analytics(date_from, date_to)
    payload["report"] = "collector_sla_metrics"
    return payload


def clinic_ranking(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_executive_metrics()
    start, end = _period(date_from, date_to)
    clinics = _safe(lambda: ClinicProfile.query.all(), [])
    orders = _safe(
        lambda: _filter_created(MedicalOrder.query, MedicalOrder, start, end).all(),
        [],
    )
    invoices = _safe(
        lambda: _filter_created(Invoice.query, Invoice, start, end).all(),
        [],
    )
    referrals = _safe(
        lambda: _filter_created(ClinicReferral.query, ClinicReferral, start, end).all(),
        [],
    )

    orders_by_partner = Counter(o.partner_id or "UNKNOWN" for o in orders)
    revenue_by_partner: dict[str, float] = {}
    for invoice in invoices:
        if invoice.billing_status != BILLING_INVOICE_PAID:
            continue
        partner_id = invoice.partner_id or "UNKNOWN"
        revenue_by_partner[partner_id] = revenue_by_partner.get(partner_id, 0) + (invoice.total_amount or 0)

    referrals_by_clinic = Counter(r.clinic_id for r in referrals if r.clinic_id)
    rows: list[dict[str, Any]] = []
    seen_clinic_ids: set[str] = set()

    for clinic in clinics:
        partner_key = clinic.partner_id or clinic.clinic_id
        rows.append(
            {
                "clinic_id": clinic.clinic_id,
                "clinic_code": clinic.clinic_code,
                "name": clinic.name,
                "status": clinic.status,
                "orders": orders_by_partner.get(partner_key, 0),
                "revenue": round(revenue_by_partner.get(partner_key, 0), 2),
                "referrals": referrals_by_clinic.get(clinic.clinic_id, 0),
                "score": orders_by_partner.get(partner_key, 0) + referrals_by_clinic.get(clinic.clinic_id, 0),
            }
        )
        seen_clinic_ids.add(clinic.clinic_id)

    for clinic_id, referral_count in referrals_by_clinic.items():
        if clinic_id in seen_clinic_ids:
            continue
        rows.append(
            {
                "clinic_id": clinic_id,
                "clinic_code": clinic_id,
                "name": clinic_id,
                "status": "UNKNOWN",
                "orders": 0,
                "revenue": 0.0,
                "referrals": referral_count,
                "score": referral_count,
            }
        )

    rows.sort(key=lambda row: (row["revenue"], row["score"], row["orders"]), reverse=True)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index

    return {
        "report": "clinic_ranking",
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "read_only": True,
        "clinics_ranked": len(rows),
        "rankings": rows[:25],
    }


def doctor_ranking(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_executive_metrics()
    start, end = _period(date_from, date_to)
    doctors = _safe(lambda: DoctorProfile.query.all(), [])
    referrals = _safe(
        lambda: _filter_created(ClinicReferral.query, ClinicReferral, start, end).all(),
        [],
    )
    approvals = _safe(
        lambda: _filter_created(
            TestResult.query.filter(TestResult.approval_status == "APPROVED"),
            TestResult,
            start,
            end,
        ).all(),
        [],
    )

    referrals_by_doctor = Counter(r.doctor_id for r in referrals if r.doctor_id)
    rows: list[dict[str, Any]] = []
    seen_doctor_ids: set[str] = set()

    for doctor in doctors:
        approval_count = sum(
            1
            for result in approvals
            if result.doctor_license == doctor.license_number or result.approved_by == doctor.full_name
        )
        referral_count = referrals_by_doctor.get(doctor.doctor_id, 0)
        rows.append(
            {
                "doctor_id": doctor.doctor_id,
                "doctor_code": doctor.doctor_code,
                "name": doctor.full_name,
                "specialty": doctor.specialty_primary,
                "status": doctor.status,
                "referrals": referral_count,
                "approvals": approval_count,
                "score": referral_count + approval_count,
            }
        )
        seen_doctor_ids.add(doctor.doctor_id)

    for doctor_id, referral_count in referrals_by_doctor.items():
        if doctor_id in seen_doctor_ids:
            continue
        rows.append(
            {
                "doctor_id": doctor_id,
                "doctor_code": doctor_id,
                "name": doctor_id,
                "specialty": None,
                "status": "UNKNOWN",
                "referrals": referral_count,
                "approvals": 0,
                "score": referral_count,
            }
        )

    rows.sort(key=lambda row: (row["score"], row["approvals"], row["referrals"]), reverse=True)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index

    return {
        "report": "doctor_ranking",
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "read_only": True,
        "doctors_ranked": len(rows),
        "rankings": rows[:25],
    }


def revenue_forecast(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_executive_metrics()
    start, end = _period(date_from, date_to)
    revenue = revenue_analytics(date_from, date_to)
    crm = CrmDashboardService.get_dashboard()

    span_days = max((end - start).days, 1)
    gross = float(revenue.get("gross_revenue", 0) or 0)
    daily_average = round(gross / span_days, 2)
    trend_projection_30d = round(daily_average * 30, 2)
    pipeline_forecast = float(crm["summary"].get("revenue_forecast", 0) or 0)
    monthly_sales = float(crm["summary"].get("monthly_sales", 0) or 0)

    return {
        "report": "revenue_forecast",
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "read_only": True,
        "historical": {
            "gross_revenue": gross,
            "daily_average": daily_average,
            "invoices_paid": revenue.get("invoices_paid", 0),
        },
        "forecast": {
            "pipeline_opportunities": pipeline_forecast,
            "trend_projection_30d": trend_projection_30d,
            "monthly_sales_won": monthly_sales,
            "combined_estimate": round(max(trend_projection_30d, pipeline_forecast), 2),
        },
        "methodology": "CRM pipeline plus trailing revenue run-rate",
    }


def executive_metrics_dashboard() -> dict[str, Any]:
    ensure_executive_metrics()
    revenue = revenue_metrics()
    orders = orders_metrics()
    growth = growth_metrics()
    lab = lab_sla_metrics()
    forecast = revenue_forecast()
    clinics = clinic_ranking()
    doctors = doctor_ranking()
    return {
        "report": "executive_metrics_dashboard",
        "read_only": True,
        "status": "OK",
        "gross_revenue": revenue.get("gross_revenue", 0),
        "orders_total": orders.get("orders_total", 0),
        "revenue_growth_percent": growth["growth"]["revenue_percent"],
        "orders_growth_percent": growth["growth"]["orders_percent"],
        "lab_sla_compliance_percent": lab["period_summary"]["sla_compliance_percent"],
        "revenue_forecast_estimate": forecast["forecast"]["combined_estimate"],
        "clinics_ranked": clinics["clinics_ranked"],
        "doctors_ranked": doctors["doctors_ranked"],
    }


def executive_metrics_readiness_report() -> dict[str, Any]:
    dashboard = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "5.9",
        "sprint": "Executive Metrics",
        "platform": dashboard["platform"],
        "status": dashboard["status"],
        "summary": dashboard["summary"],
        "features": list(FEATURES),
        "sections": {
            "revenue": revenue_metrics(),
            "tat": tat_metrics(),
            "orders": orders_metrics(),
            "growth": growth_metrics(),
            "lab_sla": lab_sla_metrics(),
            "collector_sla": collector_sla_metrics(),
            "clinic_ranking": clinic_ranking(),
            "doctor_ranking": doctor_ranking(),
            "revenue_forecast": revenue_forecast(),
        },
        "legacy_routes": [
            "/enterprise-analytics",
            "/executive-v9",
            "/api/v1/enterprise-analytics/dashboard",
            "/api/v1/dashboard/summary",
        ],
    }


def dashboard_payload(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_executive_metrics()
    dash = executive_metrics_dashboard()
    revenue = revenue_metrics(date_from, date_to)
    orders = orders_metrics(date_from, date_to)
    growth = growth_metrics(date_from, date_to)
    lab = lab_sla_metrics(date_from, date_to)
    collector = collector_sla_metrics(date_from, date_to)
    forecast = revenue_forecast(date_from, date_to)
    return {
        "platform": "Executive Metrics",
        "phase": "5.9",
        "sprint": "Executive Metrics",
        "status": dash["status"],
        "read_only": True,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "gross_revenue": revenue.get("gross_revenue", 0),
            "orders_total": orders.get("orders_total", 0),
            "revenue_growth_percent": growth["growth"]["revenue_percent"],
            "orders_growth_percent": growth["growth"]["orders_percent"],
            "lab_sla_compliance_percent": lab["period_summary"]["sla_compliance_percent"],
            "collector_sla_compliant": collector.get("collectors_sla_compliant", 0),
            "revenue_forecast_estimate": forecast["forecast"]["combined_estimate"],
            "clinics_ranked": dash["clinics_ranked"],
            "doctors_ranked": dash["doctors_ranked"],
        },
        "features": list(FEATURES),
    }
