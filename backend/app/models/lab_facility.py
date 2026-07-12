from datetime import datetime
import uuid

from app.extensions.db import db


class LabShift(db.Model):
    __tablename__ = "lab_shifts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shift_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    supervisor = db.Column(db.String(255))
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "shift_code": self.shift_code,
            "name": self.name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "supervisor": self.supervisor,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LabBench(db.Model):
    __tablename__ = "lab_benches"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bench_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(100))
    location = db.Column(db.String(255))
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "bench_code": self.bench_code,
            "name": self.name,
            "department": self.department,
            "location": self.location,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Analyzer(db.Model):
    __tablename__ = "lab_analyzers"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analyzer_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    model = db.Column(db.String(100))
    manufacturer = db.Column(db.String(100))
    lab_bench_id = db.Column(db.String(36), db.ForeignKey("lab_benches.id"))
    status = db.Column(db.String(50), default="ACTIVE")
    organization_id = db.Column(db.String(36), index=True)
    laboratory_id = db.Column(db.String(36))
    vendor = db.Column(db.String(100))
    serial_number = db.Column(db.String(100))
    protocol = db.Column(db.String(30), default="SIMULATOR")
    connection_mode = db.Column(db.String(30))
    host = db.Column(db.String(255))
    port = db.Column(db.Integer)
    last_seen_at = db.Column(db.DateTime)
    firmware_version = db.Column(db.String(50))
    software_version = db.Column(db.String(50))
    calibration_status = db.Column(db.String(30))
    maintenance_status = db.Column(db.String(30))
    result_mode = db.Column(db.String(30), default="PRELIMINARY")
    enabled = db.Column(db.Boolean, default=True)
    utilization_percent = db.Column(db.Float, default=0)
    last_run_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "analyzer_code": self.analyzer_code,
            "name": self.name,
            "model": self.model,
            "manufacturer": self.manufacturer,
            "lab_bench_id": self.lab_bench_id,
            "status": self.status,
            "organization_id": self.organization_id,
            "protocol": self.protocol,
            "vendor": self.vendor or self.manufacturer,
            "serial_number": self.serial_number,
            "enabled": self.enabled,
            "utilization_percent": self.utilization_percent,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
