from datetime import datetime
import uuid

from app.extensions.db import db


class ReportDefinition(db.Model):
    __tablename__ = "report_definitions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    definition_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    default_format = db.Column(db.String(20), default="JSON")
    config_json = db.Column(db.Text, default="{}")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "definition_code": self.definition_code,
            "name": self.name,
            "report_type": self.report_type,
            "description": self.description,
            "default_format": self.default_format,
            "config_json": self.config_json,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ReportJob(db.Model):
    __tablename__ = "report_jobs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_code = db.Column(db.String(50), unique=True, nullable=False)
    definition_id = db.Column(db.String(36), db.ForeignKey("report_definitions.id"))
    report_type = db.Column(db.String(50), nullable=False)
    output_format = db.Column(db.String(20), default="JSON")
    status = db.Column(db.String(50), default="PENDING")
    file_path = db.Column(db.String(500))
    payload_json = db.Column(db.Text)
    error_message = db.Column(db.Text)
    requested_by = db.Column(db.String(255), default="SYSTEM")
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "job_code": self.job_code,
            "definition_id": self.definition_id,
            "report_type": self.report_type,
            "output_format": self.output_format,
            "status": self.status,
            "file_path": self.file_path,
            "payload_json": self.payload_json,
            "error_message": self.error_message,
            "requested_by": self.requested_by,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ReportSchedule(db.Model):
    __tablename__ = "report_schedules"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    schedule_code = db.Column(db.String(50), unique=True, nullable=False)
    definition_id = db.Column(db.String(36), db.ForeignKey("report_definitions.id"))
    report_type = db.Column(db.String(50), nullable=False)
    cadence = db.Column(db.String(20), nullable=False)
    output_format = db.Column(db.String(20), default="PDF")
    recipient_emails = db.Column(db.Text)
    next_run_at = db.Column(db.DateTime)
    last_run_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    config_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "schedule_code": self.schedule_code,
            "definition_id": self.definition_id,
            "report_type": self.report_type,
            "cadence": self.cadence,
            "output_format": self.output_format,
            "recipient_emails": self.recipient_emails,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "is_active": self.is_active,
            "config_json": self.config_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DashboardWidget(db.Model):
    __tablename__ = "dashboard_widgets"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    widget_code = db.Column(db.String(50), unique=True, nullable=False)
    widget_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    dashboard_role = db.Column(db.String(50), default="EXECUTIVE")
    config_json = db.Column(db.Text, default="{}")
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "widget_code": self.widget_code,
            "widget_type": self.widget_type,
            "title": self.title,
            "dashboard_role": self.dashboard_role,
            "config_json": self.config_json,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DashboardLayout(db.Model):
    __tablename__ = "dashboard_layouts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    layout_code = db.Column(db.String(50), unique=True, nullable=False)
    dashboard_role = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    widget_ids_json = db.Column(db.Text, default="[]")
    config_json = db.Column(db.Text, default="{}")
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "layout_code": self.layout_code,
            "dashboard_role": self.dashboard_role,
            "name": self.name,
            "widget_ids_json": self.widget_ids_json,
            "config_json": self.config_json,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class KPIRecord(db.Model):
    __tablename__ = "kpi_records"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    record_code = db.Column(db.String(50), unique=True, nullable=False)
    period_type = db.Column(db.String(20), nullable=False)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    kpi_code = db.Column(db.String(50), nullable=False)
    kpi_value = db.Column(db.Float, default=0)
    dimension = db.Column(db.String(50))
    metadata_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "record_code": self.record_code,
            "period_type": self.period_type,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "kpi_code": self.kpi_code,
            "kpi_value": self.kpi_value,
            "dimension": self.dimension,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MetricSnapshot(db.Model):
    __tablename__ = "metric_snapshots"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    snapshot_code = db.Column(db.String(50), unique=True, nullable=False)
    metric_domain = db.Column(db.String(50), nullable=False)
    period_type = db.Column(db.String(20), nullable=False)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    metrics_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "snapshot_code": self.snapshot_code,
            "metric_domain": self.metric_domain,
            "period_type": self.period_type,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "metrics_json": self.metrics_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RevenueAnalytics(db.Model):
    __tablename__ = "revenue_analytics"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analytics_code = db.Column(db.String(50), unique=True, nullable=False)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    gross_revenue = db.Column(db.Float, default=0)
    net_revenue = db.Column(db.Float, default=0)
    invoice_count = db.Column(db.Integer, default=0)
    partner_id = db.Column(db.String(36))
    clinic_id = db.Column(db.String(36))
    metrics_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "analytics_code": self.analytics_code,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "gross_revenue": self.gross_revenue,
            "net_revenue": self.net_revenue,
            "invoice_count": self.invoice_count,
            "partner_id": self.partner_id,
            "clinic_id": self.clinic_id,
            "metrics_json": self.metrics_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LabAnalytics(db.Model):
    __tablename__ = "lab_analytics"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analytics_code = db.Column(db.String(50), unique=True, nullable=False)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    lab_partner_id = db.Column(db.String(36))
    tests_total = db.Column(db.Integer, default=0)
    tat_avg_hours = db.Column(db.Float, default=0)
    critical_rate = db.Column(db.Float, default=0)
    pending_reviews = db.Column(db.Integer, default=0)
    metrics_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "analytics_code": self.analytics_code,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "lab_partner_id": self.lab_partner_id,
            "tests_total": self.tests_total,
            "tat_avg_hours": self.tat_avg_hours,
            "critical_rate": self.critical_rate,
            "pending_reviews": self.pending_reviews,
            "metrics_json": self.metrics_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CollectorAnalytics(db.Model):
    __tablename__ = "collector_analytics"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analytics_code = db.Column(db.String(50), unique=True, nullable=False)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    collector_id = db.Column(db.String(36))
    orders_assigned = db.Column(db.Integer, default=0)
    orders_completed = db.Column(db.Integer, default=0)
    utilization_rate = db.Column(db.Float, default=0)
    transport_time_avg_minutes = db.Column(db.Float, default=0)
    metrics_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "analytics_code": self.analytics_code,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "collector_id": self.collector_id,
            "orders_assigned": self.orders_assigned,
            "orders_completed": self.orders_completed,
            "utilization_rate": self.utilization_rate,
            "transport_time_avg_minutes": self.transport_time_avg_minutes,
            "metrics_json": self.metrics_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PartnerAnalytics(db.Model):
    __tablename__ = "partner_analytics"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analytics_code = db.Column(db.String(50), unique=True, nullable=False)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    partner_id = db.Column(db.String(36))
    orders_total = db.Column(db.Integer, default=0)
    revenue_total = db.Column(db.Float, default=0)
    sla_compliance_rate = db.Column(db.Float, default=0)
    metrics_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "analytics_code": self.analytics_code,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "partner_id": self.partner_id,
            "orders_total": self.orders_total,
            "revenue_total": self.revenue_total,
            "sla_compliance_rate": self.sla_compliance_rate,
            "metrics_json": self.metrics_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ClinicAnalytics(db.Model):
    __tablename__ = "clinic_analytics"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analytics_code = db.Column(db.String(50), unique=True, nullable=False)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    clinic_id = db.Column(db.String(36))
    orders_total = db.Column(db.Integer, default=0)
    revenue_total = db.Column(db.Float, default=0)
    patient_count = db.Column(db.Integer, default=0)
    metrics_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "analytics_code": self.analytics_code,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "clinic_id": self.clinic_id,
            "orders_total": self.orders_total,
            "revenue_total": self.revenue_total,
            "patient_count": self.patient_count,
            "metrics_json": self.metrics_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
