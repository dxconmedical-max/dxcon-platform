import csv
import io
import json
import os
import uuid
from datetime import datetime, timedelta

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.core.statuses import (
    REPORT_FORMAT_CSV,
    REPORT_FORMAT_EXCEL,
    REPORT_FORMAT_JSON,
    REPORT_FORMAT_PDF,
    REPORT_JOB_COMPLETED,
    REPORT_JOB_FAILED,
    REPORT_JOB_PENDING,
    REPORT_JOB_RUNNING,
    REPORT_SCHEDULE_DAILY,
    REPORT_SCHEDULE_MONTHLY,
    REPORT_SCHEDULE_QUARTERLY,
    REPORT_SCHEDULE_WEEKLY,
    REPORT_SCHEDULE_YEARLY,
    REPORT_TYPE_EXECUTIVE,
    REPORT_TYPE_KPI,
    REPORT_TYPE_OPERATIONS,
    REPORT_TYPE_REVENUE,
    VALID_REPORT_FORMATS,
)
from app.extensions.db import db
from app.models.reporting_platform import ReportDefinition, ReportJob, ReportSchedule
from app.services.dashboard_platform_service import DashboardPlatformService
from app.services.kpi_engine_service import KPIEngineService
from app.services.reporting_service import ExecutiveDashboardService, ReportingService


GENERATED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generated_reports")


class ReportPlatformError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ReportPlatformService:

    REPORT_BUILDERS = {
        REPORT_TYPE_KPI: lambda df, dt: KPIEngineService.compute_monthly(dt, persist=False),
        REPORT_TYPE_REVENUE: lambda df, dt: ReportingService.revenue_summary(df, dt),
        REPORT_TYPE_OPERATIONS: lambda df, dt: ReportingService.get_operations_report(df, dt),
        REPORT_TYPE_EXECUTIVE: lambda df, dt: ExecutiveDashboardService.get_dashboard(df, dt),
    }

    @staticmethod
    def ensure_definitions():
        if ReportDefinition.query.first():
            return
        defaults = [
            ("RPT-KPI", "KPI Summary", REPORT_TYPE_KPI),
            ("RPT-REV", "Revenue Summary", REPORT_TYPE_REVENUE),
            ("RPT-OPS", "Operations Report", REPORT_TYPE_OPERATIONS),
            ("RPT-EXEC", "Executive Dashboard", REPORT_TYPE_EXECUTIVE),
        ]
        for code, name, report_type in defaults:
            db.session.add(
                ReportDefinition(
                    definition_code=code,
                    name=name,
                    report_type=report_type,
                    default_format=REPORT_FORMAT_JSON,
                )
            )
        db.session.commit()

    @staticmethod
    def list_reports(page=1, page_size=50):
        ReportPlatformService.ensure_definitions()
        query = ReportDefinition.query.filter_by(is_active=True)
        total = query.count()
        rows = query.order_by(ReportDefinition.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "definitions": [row.to_dict() for row in rows],
        }

    @staticmethod
    def _render_content(payload, output_format):
        if output_format == REPORT_FORMAT_JSON:
            return json.dumps(payload, indent=2), "application/json", ".json"
        if output_format == REPORT_FORMAT_CSV:
            buffer = io.StringIO()
            if isinstance(payload, dict):
                flat = {k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in payload.items()}
                writer = csv.DictWriter(buffer, fieldnames=list(flat.keys()))
                writer.writeheader()
                writer.writerow(flat)
            else:
                buffer.write(str(payload))
            return buffer.getvalue(), "text/csv", ".csv"
        if output_format == REPORT_FORMAT_EXCEL:
            buffer = io.StringIO()
            buffer.write("\ufeff")
            if isinstance(payload, dict):
                for key, value in payload.items():
                    buffer.write(f"{key}\t{json.dumps(value) if isinstance(value, (dict, list)) else value}\n")
            return buffer.getvalue(), "application/vnd.ms-excel", ".xlsx"
        if output_format == REPORT_FORMAT_PDF:
            os.makedirs(GENERATED_DIR, exist_ok=True)
            filename = f"DxCon_Report_{uuid.uuid4().hex[:8]}.pdf"
            path = os.path.join(GENERATED_DIR, filename)
            pdf = canvas.Canvas(path, pagesize=A4)
            pdf.setFont("Helvetica", 12)
            pdf.drawString(50, 800, "DxCon Analytics Report")
            y = 770
            text = json.dumps(payload, indent=2)[:3500]
            for line in text.splitlines():
                if y < 50:
                    pdf.showPage()
                    y = 800
                pdf.drawString(50, y, line[:110])
                y -= 14
            pdf.save()
            return path, "application/pdf", ".pdf"
        raise ReportPlatformError(f"Unsupported format: {output_format}", 400)

    @staticmethod
    def generate(data, actor_email="SYSTEM"):
        ReportPlatformService.ensure_definitions()
        report_type = data.get("report_type", REPORT_TYPE_KPI)
        output_format = (data.get("format") or REPORT_FORMAT_JSON).upper()
        if output_format not in VALID_REPORT_FORMATS:
            raise ReportPlatformError(f"Invalid format. Use one of {VALID_REPORT_FORMATS}", 400)

        builder = ReportPlatformService.REPORT_BUILDERS.get(report_type)
        if not builder:
            raise ReportPlatformError(f"Unsupported report type: {report_type}", 400)

        job = ReportJob(
            job_code=f"JOB-{uuid.uuid4().hex[:10].upper()}",
            report_type=report_type,
            output_format=output_format,
            status=REPORT_JOB_RUNNING,
            requested_by=actor_email,
            started_at=datetime.utcnow(),
        )
        db.session.add(job)
        db.session.flush()

        try:
            payload = builder(data.get("date_from"), data.get("date_to"))
            content, mime_type, ext = ReportPlatformService._render_content(payload, output_format)
            file_path = content if output_format == REPORT_FORMAT_PDF else None
            if output_format != REPORT_FORMAT_PDF:
                os.makedirs(GENERATED_DIR, exist_ok=True)
                file_path = os.path.join(GENERATED_DIR, f"{job.job_code}{ext}")
                with open(file_path, "w", encoding="utf-8") as handle:
                    handle.write(content if isinstance(content, str) else str(content))
            job.status = REPORT_JOB_COMPLETED
            job.file_path = file_path
            job.payload_json = json.dumps(payload) if output_format == REPORT_FORMAT_JSON else None
            job.completed_at = datetime.utcnow()
            db.session.commit()
            return job, payload
        except Exception as exc:
            job.status = REPORT_JOB_FAILED
            job.error_message = str(exc)
            job.completed_at = datetime.utcnow()
            db.session.commit()
            raise ReportPlatformError(str(exc), 500) from exc

    @staticmethod
    def history(page=1, page_size=50, report_type=None):
        query = ReportJob.query
        if report_type:
            query = query.filter(ReportJob.report_type == report_type)
        total = query.count()
        rows = query.order_by(ReportJob.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "jobs": [row.to_dict() for row in rows],
        }

    @staticmethod
    def download(job_id):
        job = ReportJob.query.get(job_id)
        if not job:
            raise ReportPlatformError("Report job not found", 404)
        if job.status != REPORT_JOB_COMPLETED:
            raise ReportPlatformError("Report job is not completed", 409)
        if job.file_path and os.path.exists(job.file_path):
            with open(job.file_path, "r", encoding="utf-8", errors="ignore") as handle:
                content = handle.read()
        elif job.payload_json:
            content = job.payload_json
        else:
            raise ReportPlatformError("Report content unavailable", 404)
        return {
            "job": job.to_dict(),
            "content": content,
            "format": job.output_format,
        }

    @staticmethod
    def _next_run(cadence, anchor=None):
        anchor = anchor or datetime.utcnow()
        mapping = {
            REPORT_SCHEDULE_DAILY: timedelta(days=1),
            REPORT_SCHEDULE_WEEKLY: timedelta(days=7),
            REPORT_SCHEDULE_MONTHLY: timedelta(days=30),
            REPORT_SCHEDULE_QUARTERLY: timedelta(days=90),
            REPORT_SCHEDULE_YEARLY: timedelta(days=365),
        }
        return anchor + mapping.get(cadence, timedelta(days=1))

    @staticmethod
    def create_schedule(data, actor_email="SYSTEM"):
        ReportPlatformService.ensure_definitions()
        cadence = (data.get("cadence") or REPORT_SCHEDULE_DAILY).upper()
        report_type = data.get("report_type", REPORT_TYPE_KPI)
        schedule = ReportSchedule(
            schedule_code=f"SCH-{uuid.uuid4().hex[:10].upper()}",
            report_type=report_type,
            cadence=cadence,
            output_format=(data.get("format") or REPORT_FORMAT_PDF).upper(),
            recipient_emails=",".join(data.get("recipients") or data.get("recipient_emails") or []),
            next_run_at=ReportPlatformService._next_run(cadence),
            config_json=json.dumps(data.get("config") or {}),
        )
        db.session.add(schedule)
        db.session.commit()
        return schedule

    @staticmethod
    def list_schedules(page=1, page_size=50):
        total = ReportSchedule.query.count()
        rows = (
            ReportSchedule.query.order_by(ReportSchedule.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "schedules": [row.to_dict() for row in rows],
        }

    @staticmethod
    def run_due_schedules():
        now = datetime.utcnow()
        due = ReportSchedule.query.filter(
            ReportSchedule.is_active.is_(True),
            ReportSchedule.next_run_at <= now,
        ).all()
        results = []
        for schedule in due:
            job, payload = ReportPlatformService.generate(
                {
                    "report_type": schedule.report_type,
                    "format": schedule.output_format,
                }
            )
            email_payload = {
                "to": schedule.recipient_emails.split(",") if schedule.recipient_emails else [],
                "subject": f"DxCon Scheduled Report - {schedule.report_type}",
                "body": f"Report {job.job_code} generated at {datetime.utcnow().isoformat()}",
                "attachment_path": job.file_path,
                "summary": payload if isinstance(payload, dict) else {"data": str(payload)[:500]},
            }
            schedule.last_run_at = now
            schedule.next_run_at = ReportPlatformService._next_run(schedule.cadence, now)
            results.append({"schedule": schedule.to_dict(), "job": job.to_dict(), "email_payload": email_payload})
        db.session.commit()
        return results
