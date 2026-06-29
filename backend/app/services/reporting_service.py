import json
import uuid
from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy import func

from app.core.statuses import (
    BILLING_INVOICE_PAID,
    KPI_CODE_COLLECTOR,
    KPI_CODE_DAILY_BOOKINGS,
    KPI_CODE_ORDERS,
    KPI_CODE_PARTNER,
    KPI_CODE_RESULTS,
    KPI_CODE_REVENUE,
    KPI_CODE_SAMPLES,
    KPI_CODE_SLA,
    REPORT_TYPE_COLLECTORS,
    REPORT_TYPE_EXECUTIVE,
    REPORT_TYPE_KPI,
    REPORT_TYPE_OPERATIONS,
    REPORT_TYPE_PARTNERS,
    REPORT_TYPE_REVENUE,
)
from app.extensions.db import db
from app.models.booking_assignment import BookingAssignment
from app.models.invoice import Invoice
from app.models.kpi_event import KPIEvent
from app.models.marketplace_booking import MarketplaceBooking
from app.models.medical_order import MedicalOrder
from app.models.medical_sample import Sample
from app.models.partner import Partner
from app.models.payment_record import PaymentRecord
from app.models.report_snapshot import ReportSnapshot
from app.models.result_file import ResultFile
from app.models.test_result import TestResult


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00").split("+")[0])
    except ValueError:
        return None


def _date_range(date_from=None, date_to=None):
    end = _parse_date(date_to) or datetime.utcnow()
    start = _parse_date(date_from) or (end - timedelta(days=30))
    if start > end:
        start, end = end, start
    return start, end


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default if default is not None else 0


def _status_distribution(query, status_field):
    rows = _safe(lambda: query.all(), [])
    counts = Counter(getattr(row, status_field, "UNKNOWN") or "UNKNOWN" for row in rows)
    return dict(counts)


def _filter_created(query, model, start, end):
    if hasattr(model, "created_at"):
        return query.filter(model.created_at >= start, model.created_at <= end)
    return query


class KPIService:

    @staticmethod
    def record_event(kpi_code, kpi_value, dimension=None, reference_id=None, metadata=None):
        event = KPIEvent(
            event_code=f"KPI-{uuid.uuid4().hex[:10].upper()}",
            kpi_code=kpi_code,
            kpi_value=kpi_value,
            dimension=dimension,
            reference_id=reference_id,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.session.add(event)
        db.session.commit()
        return event

    @staticmethod
    def list_events(kpi_code=None, date_from=None, date_to=None):
        start, end = _date_range(date_from, date_to)
        query = KPIEvent.query.filter(KPIEvent.created_at >= start, KPIEvent.created_at <= end)
        if kpi_code:
            query = query.filter(KPIEvent.kpi_code == kpi_code)
        return query.order_by(KPIEvent.created_at.desc()).all()

    @staticmethod
    def get_kpi_summary(date_from=None, date_to=None):
        start, end = _date_range(date_from, date_to)

        bookings = _safe(
            lambda: _filter_created(MarketplaceBooking.query, MarketplaceBooking, start, end).count()
        )
        orders = _safe(
            lambda: _filter_created(MedicalOrder.query, MedicalOrder, start, end).count()
        )
        paid_invoices = _safe(
            lambda: _filter_created(
                Invoice.query.filter(Invoice.billing_status == BILLING_INVOICE_PAID),
                Invoice,
                start,
                end,
            ).count()
        )
        revenue = _safe(
            lambda: db.session.query(func.coalesce(func.sum(Invoice.total_amount), 0))
            .filter(
                Invoice.billing_status == BILLING_INVOICE_PAID,
                Invoice.created_at >= start,
                Invoice.created_at <= end,
            )
            .scalar()
        )
        samples = _safe(
            lambda: _filter_created(Sample.query, Sample, start, end).count()
        )
        results = _safe(lambda: TestResult.query.count()) + _safe(lambda: ResultFile.query.count())

        summary = {
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "daily_bookings": bookings,
            "orders_total": orders,
            "invoices_paid": paid_invoices,
            "revenue_total": float(revenue or 0),
            "samples_total": samples,
            "results_total": results,
        }

        KPIService.record_event(KPI_CODE_DAILY_BOOKINGS, bookings, dimension="PLATFORM")
        KPIService.record_event(KPI_CODE_ORDERS, orders, dimension="PLATFORM")
        KPIService.record_event(KPI_CODE_REVENUE, float(revenue or 0), dimension="PLATFORM")
        KPIService.record_event(KPI_CODE_SAMPLES, samples, dimension="PLATFORM")
        KPIService.record_event(KPI_CODE_RESULTS, results, dimension="PLATFORM")

        return summary


class ReportingService:

    @staticmethod
    def save_snapshot(report_type, payload, period_start=None, period_end=None):
        snapshot = ReportSnapshot(
            snapshot_code=f"RPT-{uuid.uuid4().hex[:10].upper()}",
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            payload_json=json.dumps(payload),
        )
        db.session.add(snapshot)
        db.session.commit()
        return snapshot

    @staticmethod
    def daily_booking_report(date_from=None, date_to=None):
        start, end = _date_range(date_from, date_to)
        bookings = _safe(
            lambda: _filter_created(MarketplaceBooking.query, MarketplaceBooking, start, end).all(),
            [],
        )
        by_status = _status_distribution(
            _filter_created(MarketplaceBooking.query, MarketplaceBooking, start, end),
            "status",
        )
        return {
            "report": "daily_bookings",
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "total": len(bookings),
            "by_status": by_status,
        }

    @staticmethod
    def revenue_summary(date_from=None, date_to=None):
        start, end = _date_range(date_from, date_to)
        invoices = _safe(
            lambda: _filter_created(Invoice.query, Invoice, start, end).all(),
            [],
        )
        payments = _safe(
            lambda: _filter_created(PaymentRecord.query, PaymentRecord, start, end).all(),
            [],
        )
        gross = sum(inv.total_amount or 0 for inv in invoices if inv.billing_status == BILLING_INVOICE_PAID)
        paid_count = len([inv for inv in invoices if inv.billing_status == BILLING_INVOICE_PAID])
        refunded = len([inv for inv in invoices if inv.billing_status == "REFUNDED"])
        payment_total = sum(p.amount or 0 for p in payments if getattr(p, "status", "") == "COMPLETED")

        return {
            "report": "revenue_summary",
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "gross_revenue": gross,
            "payment_total": payment_total,
            "invoices_paid": paid_count,
            "invoices_refunded": refunded,
            "invoices_total": len(invoices),
        }

    @staticmethod
    def collector_productivity(date_from=None, date_to=None):
        start, end = _date_range(date_from, date_to)
        orders = _safe(
            lambda: _filter_created(MedicalOrder.query, MedicalOrder, start, end).all(),
            [],
        )
        assignments = _safe(
            lambda: _filter_created(BookingAssignment.query, BookingAssignment, start, end).all(),
            [],
        )

        by_collector = Counter()
        completed_by_collector = Counter()
        for order in orders:
            cid = order.collector_id or "UNASSIGNED"
            by_collector[cid] += 1
            if order.status in ("COMPLETED", "COLLECTED", "IN_LAB"):
                completed_by_collector[cid] += 1

        assignment_counts = Counter(a.collector_id or "UNASSIGNED" for a in assignments)

        collectors = []
        for collector_id in set(list(by_collector.keys()) + list(assignment_counts.keys())):
            assigned = by_collector.get(collector_id, 0)
            completed = completed_by_collector.get(collector_id, 0)
            collectors.append(
                {
                    "collector_id": collector_id,
                    "orders_assigned": assigned,
                    "orders_completed": completed,
                    "assignments_total": assignment_counts.get(collector_id, 0),
                    "completion_rate": round((completed / assigned) * 100, 2) if assigned else 0,
                }
            )

        return {
            "report": "collector_productivity",
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "collectors_total": len([c for c in collectors if c["collector_id"] != "UNASSIGNED"]),
            "collectors": sorted(collectors, key=lambda c: c["orders_assigned"], reverse=True),
        }

    @staticmethod
    def partner_performance(date_from=None, date_to=None):
        start, end = _date_range(date_from, date_to)
        partners = _safe(lambda: Partner.query.all(), [])
        orders = _safe(
            lambda: _filter_created(MedicalOrder.query, MedicalOrder, start, end).all(),
            [],
        )
        invoices = _safe(
            lambda: _filter_created(Invoice.query, Invoice, start, end).all(),
            [],
        )

        by_partner = Counter(o.partner_id or "UNKNOWN" for o in orders)
        revenue_by_partner = {}
        for inv in invoices:
            if inv.billing_status != BILLING_INVOICE_PAID:
                continue
            pid = inv.partner_id or "UNKNOWN"
            revenue_by_partner[pid] = revenue_by_partner.get(pid, 0) + (inv.total_amount or 0)

        partner_rows = []
        for partner in partners:
            pid = partner.id
            total_orders = by_partner.get(pid, 0)
            completed = len(
                [
                    o
                    for o in orders
                    if o.partner_id == pid and o.status in ("COMPLETED", "IN_LAB", "RESULT_READY")
                ]
            )
            partner_rows.append(
                {
                    "partner_id": pid,
                    "partner_code": partner.partner_code,
                    "display_name": partner.display_name,
                    "orders_total": total_orders,
                    "orders_completed": completed,
                    "revenue": revenue_by_partner.get(pid, 0),
                    "completion_rate": round((completed / total_orders) * 100, 2) if total_orders else 0,
                }
            )

        return {
            "report": "partner_performance",
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "partners_total": len(partner_rows),
            "partners": sorted(partner_rows, key=lambda p: p["orders_total"], reverse=True),
        }

    @staticmethod
    def sla_performance(date_from=None, date_to=None):
        start, end = _date_range(date_from, date_to)
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

        KPIService.record_event(KPI_CODE_SLA, platform_compliance, dimension="PLATFORM")

        return {
            "report": "sla_performance",
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "platform_sla_compliance_rate": platform_compliance,
            "partners": rows,
        }

    @staticmethod
    def order_status_distribution(date_from=None, date_to=None):
        start, end = _date_range(date_from, date_to)
        query = _filter_created(MedicalOrder.query, MedicalOrder, start, end)
        by_status = _status_distribution(query, "status")
        total = _safe(lambda: query.count())
        return {
            "report": "order_status_distribution",
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "total": total,
            "by_status": by_status,
        }

    @staticmethod
    def sample_collection_status(date_from=None, date_to=None):
        start, end = _date_range(date_from, date_to)
        query = _filter_created(Sample.query, Sample, start, end)
        by_status = _status_distribution(query, "status")
        total = _safe(lambda: query.count())
        return {
            "report": "sample_collection_status",
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "total": total,
            "by_status": by_status,
        }

    @staticmethod
    def result_status(date_from=None, date_to=None):
        start, end = _date_range(date_from, date_to)
        test_results = _safe(lambda: TestResult.query.all(), [])
        result_files = _safe(
            lambda: _filter_created(ResultFile.query, ResultFile, start, end).all(),
            [],
        )
        by_approval = Counter(r.approval_status or "UNKNOWN" for r in test_results)
        return {
            "report": "result_status",
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "test_results_total": len(test_results),
            "result_files_total": len(result_files),
            "by_approval_status": dict(by_approval),
        }

    @staticmethod
    def get_operations_report(date_from=None, date_to=None):
        payload = {
            "daily_bookings": ReportingService.daily_booking_report(date_from, date_to),
            "order_status_distribution": ReportingService.order_status_distribution(date_from, date_to),
            "sample_collection_status": ReportingService.sample_collection_status(date_from, date_to),
            "result_status": ReportingService.result_status(date_from, date_to),
            "sla_performance": ReportingService.sla_performance(date_from, date_to),
        }
        ReportingService.save_snapshot(
            REPORT_TYPE_OPERATIONS,
            payload,
            period_start=_parse_date(date_from),
            period_end=_parse_date(date_to),
        )
        return payload


class ExecutiveDashboardService:

    @staticmethod
    def get_dashboard(date_from=None, date_to=None):
        kpi = KPIService.get_kpi_summary(date_from, date_to)
        revenue = ReportingService.revenue_summary(date_from, date_to)
        partners = ReportingService.partner_performance(date_from, date_to)
        collectors = ReportingService.collector_productivity(date_from, date_to)
        sla = ReportingService.sla_performance(date_from, date_to)

        payload = {
            "report": "executive_dashboard",
            "period_start": kpi["period_start"],
            "period_end": kpi["period_end"],
            "kpi": kpi,
            "revenue": revenue,
            "top_partners": partners["partners"][:5],
            "top_collectors": collectors["collectors"][:5],
            "sla_compliance_rate": sla["platform_sla_compliance_rate"],
        }

        ReportingService.save_snapshot(
            REPORT_TYPE_EXECUTIVE,
            payload,
            period_start=_parse_date(date_from),
            period_end=_parse_date(date_to),
        )
        KPIService.record_event(KPI_CODE_PARTNER, partners["partners_total"], dimension="EXECUTIVE")
        KPIService.record_event(KPI_CODE_COLLECTOR, collectors["collectors_total"], dimension="EXECUTIVE")

        return payload
