from datetime import datetime
import uuid

from app.extensions.db import db


class SampleAccession(db.Model):
    __tablename__ = "lab_sample_accessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    accession_code = db.Column(db.String(50), unique=True, nullable=False)
    sample_code = db.Column(db.String(50), nullable=False)
    medical_sample_id = db.Column(db.String(36), db.ForeignKey("medical_samples.id"))
    medical_order_id = db.Column(db.String(36), db.ForeignKey("medical_orders.id"))
    patient_name = db.Column(db.String(255))
    sample_type = db.Column(db.String(100))
    workflow_stage = db.Column(db.String(50), default="BOOKING")
    status = db.Column(db.String(50), default="PENDING")
    worklist_id = db.Column(db.String(36), db.ForeignKey("lab_worklists.id"))
    lab_bench_id = db.Column(db.String(36), db.ForeignKey("lab_benches.id"))
    lab_shift_id = db.Column(db.String(36), db.ForeignKey("lab_shifts.id"))
    analyzer_id = db.Column(db.String(36), db.ForeignKey("lab_analyzers.id"))
    priority = db.Column(db.String(20), default="NORMAL")
    tat_target_minutes = db.Column(db.Integer, default=240)
    received_at = db.Column(db.DateTime)
    released_at = db.Column(db.DateTime)
    assigned_technician = db.Column(db.String(255))
    assigned_pathologist = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "accession_code": self.accession_code,
            "sample_code": self.sample_code,
            "medical_sample_id": self.medical_sample_id,
            "medical_order_id": self.medical_order_id,
            "patient_name": self.patient_name,
            "sample_type": self.sample_type,
            "workflow_stage": self.workflow_stage,
            "status": self.status,
            "worklist_id": self.worklist_id,
            "lab_bench_id": self.lab_bench_id,
            "lab_shift_id": self.lab_shift_id,
            "analyzer_id": self.analyzer_id,
            "priority": self.priority,
            "tat_target_minutes": self.tat_target_minutes,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "released_at": self.released_at.isoformat() if self.released_at else None,
            "assigned_technician": self.assigned_technician,
            "assigned_pathologist": self.assigned_pathologist,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Worklist(db.Model):
    __tablename__ = "lab_worklists"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    worklist_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    lab_bench_id = db.Column(db.String(36), db.ForeignKey("lab_benches.id"))
    lab_shift_id = db.Column(db.String(36), db.ForeignKey("lab_shifts.id"))
    assigned_technician = db.Column(db.String(255))
    status = db.Column(db.String(50), default="OPEN")
    sample_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "worklist_code": self.worklist_code,
            "name": self.name,
            "lab_bench_id": self.lab_bench_id,
            "lab_shift_id": self.lab_shift_id,
            "assigned_technician": self.assigned_technician,
            "status": self.status,
            "sample_count": self.sample_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class LabWorkflowTransition(db.Model):
    __tablename__ = "lab_workflow_transitions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    accession_id = db.Column(
        db.String(36), db.ForeignKey("lab_sample_accessions.id"), nullable=False
    )
    from_stage = db.Column(db.String(50))
    to_stage = db.Column(db.String(50), nullable=False)
    actor = db.Column(db.String(255), default="SYSTEM")
    message = db.Column(db.Text)
    metadata_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "accession_id": self.accession_id,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "actor": self.actor,
            "message": self.message,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
