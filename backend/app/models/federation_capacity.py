from datetime import datetime
import uuid

from app.extensions.db import db


class CapacitySnapshot(db.Model):
    __tablename__ = "federation_capacity_snapshots"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    snapshot_code = db.Column(db.String(50), unique=True, nullable=False)
    federated_lab_id = db.Column(db.String(36), db.ForeignKey("federated_labs.id"), nullable=False)
    snapshot_date = db.Column(db.DateTime, nullable=False)
    total_capacity = db.Column(db.Integer, default=0)
    used_capacity = db.Column(db.Integer, default=0)
    remaining_capacity = db.Column(db.Integer, default=0)
    utilization_rate = db.Column(db.Float, default=0)
    metrics_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "snapshot_code": self.snapshot_code,
            "federated_lab_id": self.federated_lab_id,
            "snapshot_date": self.snapshot_date.isoformat() if self.snapshot_date else None,
            "total_capacity": self.total_capacity,
            "used_capacity": self.used_capacity,
            "remaining_capacity": self.remaining_capacity,
            "utilization_rate": self.utilization_rate,
            "metrics_json": self.metrics_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CapacityRule(db.Model):
    __tablename__ = "federation_capacity_rules"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_code = db.Column(db.String(50), unique=True, nullable=False)
    federated_lab_id = db.Column(db.String(36), db.ForeignKey("federated_labs.id"))
    max_daily_tests = db.Column(db.Integer, default=500)
    warning_threshold = db.Column(db.Float, default=0.8)
    block_threshold = db.Column(db.Float, default=0.95)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "rule_code": self.rule_code,
            "federated_lab_id": self.federated_lab_id,
            "max_daily_tests": self.max_daily_tests,
            "warning_threshold": self.warning_threshold,
            "block_threshold": self.block_threshold,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AnalyzerCapacity(db.Model):
    __tablename__ = "federation_analyzer_capacities"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analyzer_code = db.Column(db.String(50), nullable=False)
    federated_lab_id = db.Column(db.String(36), db.ForeignKey("federated_labs.id"), nullable=False)
    analyzer_name = db.Column(db.String(255), nullable=False)
    hourly_throughput = db.Column(db.Integer, default=20)
    status = db.Column(db.String(50), default="ONLINE")
    qc_status = db.Column(db.String(50), default="PASS")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "analyzer_code": self.analyzer_code,
            "federated_lab_id": self.federated_lab_id,
            "analyzer_name": self.analyzer_name,
            "hourly_throughput": self.hourly_throughput,
            "status": self.status,
            "qc_status": self.qc_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LabWorkloadSnapshot(db.Model):
    __tablename__ = "federation_lab_workload_snapshots"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    snapshot_code = db.Column(db.String(50), unique=True, nullable=False)
    federated_lab_id = db.Column(db.String(36), db.ForeignKey("federated_labs.id"), nullable=False)
    snapshot_date = db.Column(db.DateTime, nullable=False)
    pending_orders = db.Column(db.Integer, default=0)
    in_progress_tests = db.Column(db.Integer, default=0)
    completed_tests = db.Column(db.Integer, default=0)
    average_tat_hours = db.Column(db.Float, default=0)
    qc_issue_rate = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "snapshot_code": self.snapshot_code,
            "federated_lab_id": self.federated_lab_id,
            "snapshot_date": self.snapshot_date.isoformat() if self.snapshot_date else None,
            "pending_orders": self.pending_orders,
            "in_progress_tests": self.in_progress_tests,
            "completed_tests": self.completed_tests,
            "average_tat_hours": self.average_tat_hours,
            "qc_issue_rate": self.qc_issue_rate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
