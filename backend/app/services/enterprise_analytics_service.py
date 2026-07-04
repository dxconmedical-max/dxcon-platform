"""Enterprise Analytics business logic for Phase 4 Sprint 4.6."""

from __future__ import annotations

import csv
import io
from collections import Counter
from datetime import datetime
from typing import Any

from sqlalchemy import func

from app.ai_platform.metrics import AIUsageMetricsService
from app.core.statuses import (
    BILLING_INVOICE_PAID,
    INTERPRETATION_FLAG_CRITICAL,
    KPI_CODE_AI_INTERPRETATION,
    KPI_CODE_TAT,
    LAB_RESULT_REJECTED,
    MEDICAL_ORDER_REJECTED,
    MEDICAL_SAMPLE_REJECTED,
)
from app.extensions.db import db
from app.models.integration_platform import IntegrationDeadLetter, WebhookEndpoint
from app.models.lab_accession import SampleAccession
from app.models.lab_operations import CriticalResult
from app.models.lab_result import LabResult
from app.models.lab_result_item import LabResultItem
from app.models.medical_order import MedicalOrder
from app.models.medical_sample import Sample
from app.models.partner import Partner
from app.services.kpi_engine_service import KPIEngineService
from app.services.lab_dashboard_service import LabDashboardService
from app.services.reporting_service import ReportingService, _date_range, _filter_created, _safe

ANALYTICS_ROLES = ("SUPER_ADMIN", "ADMIN")

FEATURES = (
    "Revenue Analytics",
    "Lab SLA Analytics",
    "Collector SLA Analytics",
    "Partner Performance",
    "Turnaround Time Analytics",
    "Sample Rejection Analytics",
    "Critical Result Analytics",
    "AI Usage Analytics",
    "Integration Failure Analytics",
    "Executive KPI Export",
    "Verification Report",
)


class EnterpriseAnalyticsError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _period(date_from=None, date_to=None) -> tuple[datetime, datetime]:
    return _date_range(date_from, date_to)


def ensure_analytics() -> dict[str, Any]:
    return {"ready": True, "read_only": True}


def revenue_analytics(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_analytics()
    payload = ReportingService.revenue_summary(date_from, date_to)
    start, end = _period(date_from, date_to)
    from app.models.invoice import Invoice as InvoiceModel

    rows = _safe(
        lambda: db.session.query(
            InvoiceModel.partner_id,
            func.count(InvoiceModel.id),
            func.coalesce(func.sum(InvoiceModel.total_amount), 0),
        )
        .filter(
            InvoiceModel.created_at >= start,
            InvoiceModel.created_at <= end,
            InvoiceModel.billing_status == BILLING_INVOICE_PAID,
        )
        .group_by(InvoiceModel.partner_id)
        .all(),
        [],
    )
    top_partners = [
        {
            "partner_id": partner_id or "UNKNOWN",
            "invoices_paid": count,
            "revenue": float(total or 0),
        }
        for partner_id, count, total in rows
    ]
    payload["top_partners_by_revenue"] = sorted(top_partners, key=lambda r: r["revenue"], reverse=True)[:10]
    payload["read_only"] = True
    return payload


def lab_sla_analytics(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_analytics()
    start, end = _period(date_from, date_to)
    lab_dashboard = LabDashboardService.get_dashboard()
    completed = _safe(
        lambda: SampleAccession.query.filter(
            SampleAccession.received_at.isnot(None),
            SampleAccession.released_at.isnot(None),
            SampleAccession.received_at >= start,
            SampleAccession.released_at <= end,
        ).all(),
        [],
    )
    sla_met = 0
    tat_values = []
    for sample in completed:
        minutes = (sample.released_at - sample.received_at).total_seconds() / 60
        tat_values.append(minutes)
        if minutes <= (sample.tat_target_minutes or 240):
            sla_met += 1
    return {
        "report": "lab_sla_analytics",
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "read_only": True,
        "current_ops": {
            "pending_samples": lab_dashboard["pending_samples"],
            "average_tat_minutes": lab_dashboard["average_tat_minutes"],
            "sla_compliance_percent": lab_dashboard["sla_percent"],
            "critical_results_open": lab_dashboard["critical_results"],
        },
        "period_summary": {
            "accessions_completed": len(completed),
            "average_tat_minutes": round(sum(tat_values) / len(tat_values), 2) if tat_values else 0,
            "sla_compliance_percent": round((sla_met / len(completed)) * 100, 2) if completed else 0,
            "sla_breaches": max(len(completed) - sla_met, 0),
        },
    }


def collector_sla_analytics(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_analytics()
    collectors = ReportingService.collector_productivity(date_from, date_to)
    start, end = _period(date_from, date_to)
    assignments = _safe(
        lambda: _filter_created(
            MedicalOrder.query.filter(MedicalOrder.collector_id.isnot(None)),
            MedicalOrder,
            start,
            end,
        ).count()
    )
    sla_threshold = 90.0
    compliant = sum(1 for row in collectors["collectors"] if row["completion_rate"] >= sla_threshold)
    return {
        "report": "collector_sla_analytics",
        "period_start": collectors["period_start"],
        "period_end": collectors["period_end"],
        "read_only": True,
        "sla_threshold_percent": sla_threshold,
        "collectors_total": collectors["collectors_total"],
        "collectors_sla_compliant": compliant,
        "collectors": collectors["collectors"][:25],
        "active_collectors": assignments,
    }


def partner_performance(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_analytics()
    payload = ReportingService.partner_performance(date_from, date_to)
    sla = _read_only_sla_performance(date_from, date_to)
    partner_sla = {row["partner_id"]: row for row in sla["partners"]}
    for row in payload["partners"]:
        sla_row = partner_sla.get(row["partner_id"], {})
        row["sla_compliance_rate"] = sla_row.get("sla_compliance_rate", 0)
        row["sla_breaches"] = sla_row.get("breaches", 0)
    payload["read_only"] = True
    payload["platform_sla_compliance_rate"] = sla["platform_sla_compliance_rate"]
    return payload


def _read_only_sla_performance(date_from=None, date_to=None) -> dict[str, Any]:
    start, end = _period(date_from, date_to)
    partners = _safe(lambda: Partner.query.all(), [])
    orders = _safe(
        lambda: _filter_created(MedicalOrder.query, MedicalOrder, start, end).all(),
        [],
    )
    rows = []
    total_orders = len(orders) or 1
    completed = len([o for o in orders if o.status == "COMPLETED"])
    platform_compliance = round((completed / total_orders) * 100, 2)
    for partner in partners:
        partner_orders = [o for o in orders if o.partner_id == partner.id]
        partner_completed = [o for o in partner_orders if o.status == "COMPLETED"]
        total = len(partner_orders) or 1
        compliance = round((len(partner_completed) / total) * 100, 2)
        rows.append(
            {
                "partner_id": partner.id,
                "partner_code": partner.partner_code,
                "pickup_sla_minutes": partner.pickup_sla_minutes or 0,
                "response_sla_minutes": partner.response_sla_minutes or 0,
                "orders_total": len(partner_orders),
                "orders_completed": len(partner_completed),
                "sla_compliance_rate": compliance,
                "breaches": max(len(partner_orders) - len(partner_completed), 0),
            }
        )
    return {
        "report": "sla_performance",
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "platform_sla_compliance_rate": platform_compliance,
        "partners": rows,
    }


def turnaround_time_analytics(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_analytics()
    start, end = _period(date_from, date_to)
    kpi = KPIEngineService.compute_monthly(end, persist=False)
    released = _safe(
        lambda: LabResult.query.filter(
            LabResult.released_at.isnot(None),
            LabResult.released_at >= start,
            LabResult.released_at <= end,
        ).all(),
        [],
    )
    hours = []
    for result in released:
        if result.created_at and result.released_at:
            hours.append((result.released_at - result.created_at).total_seconds() / 3600)
    lab = lab_sla_analytics(date_from, date_to)
    return {
        "report": "turnaround_time_analytics",
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "read_only": True,
        "average_tat_hours": round(sum(hours) / len(hours), 2) if hours else kpi["metrics"].get(KPI_CODE_TAT, 0),
        "results_released": len(released),
        "lab_accession_tat_minutes": lab["period_summary"]["average_tat_minutes"],
        "kpi_metrics": kpi["metrics"],
    }


def sample_rejection_analytics(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_analytics()
    start, end = _period(date_from, date_to)
    order_rejections = _safe(
        lambda: _filter_created(
            MedicalOrder.query.filter_by(status=MEDICAL_ORDER_REJECTED),
            MedicalOrder,
            start,
            end,
        ).count()
    )
    sample_rejections = _safe(
        lambda: _filter_created(
            Sample.query.filter_by(status=MEDICAL_SAMPLE_REJECTED),
            Sample,
            start,
            end,
        ).count()
    )
    result_rejections = _safe(
        lambda: _filter_created(
            LabResult.query.filter_by(status=LAB_RESULT_REJECTED),
            LabResult,
            start,
            end,
        ).count()
    )
    total_orders = _safe(
        lambda: _filter_created(MedicalOrder.query, MedicalOrder, start, end).count()
    ) or 1
    total_samples = _safe(lambda: _filter_created(Sample.query, Sample, start, end).count()) or 1
    return {
        "report": "sample_rejection_analytics",
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "read_only": True,
        "rejections": {
            "orders": order_rejections,
            "samples": sample_rejections,
            "lab_results": result_rejections,
            "total": order_rejections + sample_rejections + result_rejections,
        },
        "rejection_rates": {
            "orders_percent": round((order_rejections / total_orders) * 100, 2),
            "samples_percent": round((sample_rejections / total_samples) * 100, 2),
        },
    }


def critical_result_analytics(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_analytics()
    start, end = _period(date_from, date_to)
    critical_items = _safe(
        lambda: _filter_created(
            LabResultItem.query.filter(LabResultItem.flag == INTERPRETATION_FLAG_CRITICAL),
            LabResultItem,
            start,
            end,
        ).count()
    )
    total_items = _safe(
        lambda: _filter_created(LabResultItem.query, LabResultItem, start, end).count()
    ) or 1
    open_critical = _safe(lambda: CriticalResult.query.filter_by(status="OPEN").count())
    by_status = _safe(
        lambda: dict(
            Counter(
                row.status
                for row in CriticalResult.query.filter(
                    CriticalResult.created_at >= start,
                    CriticalResult.created_at <= end,
                ).all()
            )
        ),
        {},
    )
    return {
        "report": "critical_result_analytics",
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "read_only": True,
        "critical_items": critical_items,
        "critical_rate_percent": round((critical_items / total_items) * 100, 2),
        "open_critical_results": open_critical,
        "by_status": by_status,
    }


def ai_usage_analytics(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_analytics()
    start, end = _period(date_from, date_to)
    summary = AIUsageMetricsService.summary()
    kpi = KPIEngineService.compute_monthly(end, persist=False)
    return {
        "report": "ai_usage_analytics",
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "read_only": True,
        "usage": summary,
        "interpretation_rate_percent": kpi["metrics"].get(KPI_CODE_AI_INTERPRETATION, 0),
    }


def integration_failure_analytics(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_analytics()
    start, end = _period(date_from, date_to)
    dead_letters = _safe(
        lambda: IntegrationDeadLetter.query.filter(
            IntegrationDeadLetter.created_at >= start,
            IntegrationDeadLetter.created_at <= end,
        )
        .order_by(IntegrationDeadLetter.created_at.desc())
        .limit(25)
        .all(),
        [],
    )
    total_dead_letters = _safe(lambda: IntegrationDeadLetter.query.count())
    return {
        "report": "integration_failure_analytics",
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "read_only": True,
        "hub_status": {
            "status": "OK" if total_dead_letters == 0 else "DEGRADED",
            "dead_letters_total": total_dead_letters,
            "webhooks_active": _safe(lambda: WebhookEndpoint.query.count()),
        },
        "dead_letter_count": len(dead_letters),
        "dead_letters": [row.to_dict() for row in dead_letters],
    }


def executive_kpi_export(date_from=None, date_to=None, export_format: str = "json") -> dict[str, Any]:
    ensure_analytics()
    bundle = {
        "report": "executive_kpi_export",
        "read_only": True,
        "generated_at": datetime.utcnow().isoformat(),
        "revenue": revenue_analytics(date_from, date_to),
        "lab_sla": lab_sla_analytics(date_from, date_to),
        "collector_sla": collector_sla_analytics(date_from, date_to),
        "partners": partner_performance(date_from, date_to),
        "turnaround_time": turnaround_time_analytics(date_from, date_to),
        "rejections": sample_rejection_analytics(date_from, date_to),
        "critical_results": critical_result_analytics(date_from, date_to),
        "ai_usage": ai_usage_analytics(date_from, date_to),
        "integration_failures": integration_failure_analytics(date_from, date_to),
    }
    if export_format.lower() == "csv":
        bundle["csv"] = _export_csv(bundle)
    return bundle


def _export_csv(bundle: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["section", "metric", "value"])
    revenue = bundle["revenue"]
    writer.writerow(["revenue", "gross_revenue", revenue.get("gross_revenue", 0)])
    writer.writerow(["revenue", "invoices_paid", revenue.get("invoices_paid", 0)])
    lab = bundle["lab_sla"]["period_summary"]
    writer.writerow(["lab_sla", "sla_compliance_percent", lab.get("sla_compliance_percent", 0)])
    writer.writerow(["lab_sla", "average_tat_minutes", lab.get("average_tat_minutes", 0)])
    partners = bundle["partners"]
    writer.writerow(["partners", "partners_total", partners.get("partners_total", 0)])
    writer.writerow(["partners", "platform_sla_compliance_rate", partners.get("platform_sla_compliance_rate", 0)])
    rejections = bundle["rejections"]["rejections"]
    writer.writerow(["rejections", "total", rejections.get("total", 0)])
    critical = bundle["critical_results"]
    writer.writerow(["critical_results", "critical_items", critical.get("critical_items", 0)])
    ai = bundle["ai_usage"]["usage"]["totals"]
    writer.writerow(["ai_usage", "requests", ai.get("requests", 0)])
    integration = bundle["integration_failures"]
    writer.writerow(["integration_failures", "dead_letter_count", integration.get("dead_letter_count", 0)])
    return output.getvalue()


def dashboard_payload(date_from=None, date_to=None) -> dict[str, Any]:
    ensure_analytics()
    revenue = revenue_analytics(date_from, date_to)
    lab = lab_sla_analytics(date_from, date_to)
    partners = partner_performance(date_from, date_to)
    rejections = sample_rejection_analytics(date_from, date_to)
    critical = critical_result_analytics(date_from, date_to)
    ai = ai_usage_analytics(date_from, date_to)
    integration = integration_failure_analytics(date_from, date_to)
    return {
        "platform": "Enterprise Analytics",
        "phase": "4.6",
        "sprint": "Enterprise Analytics Expansion",
        "status": "OK",
        "read_only": True,
        "summary": {
            "gross_revenue": revenue.get("gross_revenue", 0),
            "lab_sla_compliance_percent": lab["period_summary"]["sla_compliance_percent"],
            "partners_tracked": partners.get("partners_total", 0),
            "rejections_total": rejections["rejections"]["total"],
            "critical_items": critical.get("critical_items", 0),
            "ai_requests": ai["usage"]["totals"]["requests"],
            "integration_dead_letters": integration.get("dead_letter_count", 0),
        },
        "features": list(FEATURES),
    }
