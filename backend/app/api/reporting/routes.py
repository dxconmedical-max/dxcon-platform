from flask import Blueprint, request

from app.services.dashboard_platform_service import DashboardPlatformService
from app.services.report_platform_service import ReportPlatformError, ReportPlatformService
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


def _pagination_args():
    return (
        max(int(request.args.get("page", 1)), 1),
        min(max(int(request.args.get("page_size", 50)), 1), 200),
    )


@reporting_bp.route("", methods=["GET"])
def list_report_definitions():
    page, page_size = _pagination_args()
    return ReportPlatformService.list_reports(page=page, page_size=page_size)


@reporting_bp.route("/generate", methods=["POST"])
def generate_report():
    data = request.get_json(silent=True) or {}
    try:
        job, payload = ReportPlatformService.generate(
            data,
            actor_email=request.headers.get("X-User-Email", "SYSTEM"),
        )
    except ReportPlatformError as exc:
        return {"error": exc.message}, exc.status_code
    return {
        "message": "Report generated",
        "job": job.to_dict(),
        "preview": payload if isinstance(payload, dict) else {"data": str(payload)[:500]},
    }, 201


@reporting_bp.route("/history", methods=["GET"])
def report_history():
    page, page_size = _pagination_args()
    return ReportPlatformService.history(
        page=page,
        page_size=page_size,
        report_type=request.args.get("report_type"),
    )


@reporting_bp.route("/download", methods=["GET"])
def download_report():
    job_id = request.args.get("job_id")
    if not job_id:
        return {"error": "job_id is required"}, 400
    try:
        return ReportPlatformService.download(job_id)
    except ReportPlatformError as exc:
        return {"error": exc.message}, exc.status_code


@reporting_bp.route("/schedule", methods=["GET", "POST"])
def report_schedule():
    page, page_size = _pagination_args()
    if request.method == "GET":
        return ReportPlatformService.list_schedules(page=page, page_size=page_size)
    data = request.get_json(silent=True) or {}
    schedule = ReportPlatformService.create_schedule(
        data,
        actor_email=request.headers.get("X-User-Email", "SYSTEM"),
    )
    return {"message": "Schedule created", "schedule": schedule.to_dict()}, 201


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
