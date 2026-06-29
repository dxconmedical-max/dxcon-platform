from flask import Blueprint, request

from app.services.reporting_service import (
    ExecutiveDashboardService,
    KPIService,
    ReportingService,
)


reporting_bp = Blueprint(
    "reporting",
    __name__,
    url_prefix="/api/v1/reports",
)


def _date_args():
    return request.args.get("date_from"), request.args.get("date_to")


@reporting_bp.route("/kpi", methods=["GET"])
def kpi_report():
    date_from, date_to = _date_args()
    summary = KPIService.get_kpi_summary(date_from, date_to)
    ReportingService.save_snapshot(
        "KPI",
        summary,
        period_start=date_from,
        period_end=date_to,
    )
    return summary


@reporting_bp.route("/revenue", methods=["GET"])
def revenue_report():
    date_from, date_to = _date_args()
    payload = ReportingService.revenue_summary(date_from, date_to)
    ReportingService.save_snapshot("REVENUE", payload, period_start=date_from, period_end=date_to)
    return payload


@reporting_bp.route("/operations", methods=["GET"])
def operations_report():
    date_from, date_to = _date_args()
    return ReportingService.get_operations_report(date_from, date_to)


@reporting_bp.route("/partners", methods=["GET"])
def partners_report():
    date_from, date_to = _date_args()
    payload = ReportingService.partner_performance(date_from, date_to)
    ReportingService.save_snapshot("PARTNERS", payload, period_start=date_from, period_end=date_to)
    return payload


@reporting_bp.route("/collectors", methods=["GET"])
def collectors_report():
    date_from, date_to = _date_args()
    payload = ReportingService.collector_productivity(date_from, date_to)
    ReportingService.save_snapshot("COLLECTORS", payload, period_start=date_from, period_end=date_to)
    return payload


@reporting_bp.route("/executive", methods=["GET"])
def executive_report():
    date_from, date_to = _date_args()
    return ExecutiveDashboardService.get_dashboard(date_from, date_to)
