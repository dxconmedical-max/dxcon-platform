from datetime import datetime
import uuid

from app.extensions.db import db


class AnalyzerQueue(db.Model):
    __tablename__ = "lab_analyzer_queues"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    queue_code = db.Column(db.String(50), unique=True, nullable=False)
    analyzer_id = db.Column(
        db.String(36), db.ForeignKey("lab_analyzers.id"), nullable=False
    )
    accession_id = db.Column(
        db.String(36), db.ForeignKey("lab_sample_accessions.id"), nullable=False
    )
    position = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default="QUEUED")
    queued_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "queue_code": self.queue_code,
            "analyzer_id": self.analyzer_id,
            "accession_id": self.accession_id,
            "position": self.position,
            "status": self.status,
            "queued_at": self.queued_at.isoformat() if self.queued_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class QualityControl(db.Model):
    __tablename__ = "lab_quality_controls"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    qc_code = db.Column(db.String(50), unique=True, nullable=False)
    accession_id = db.Column(db.String(36), db.ForeignKey("lab_sample_accessions.id"))
    analyzer_id = db.Column(db.String(36), db.ForeignKey("lab_analyzers.id"))
    control_level = db.Column(db.String(50), default="LEVEL_1")
    test_code = db.Column(db.String(50))
    expected_value = db.Column(db.Float)
    observed_value = db.Column(db.Float)
    status = db.Column(db.String(50), default="PENDING")
    reviewed_by = db.Column(db.String(255))
    notes = db.Column(db.Text)
    performed_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "qc_code": self.qc_code,
            "accession_id": self.accession_id,
            "analyzer_id": self.analyzer_id,
            "control_level": self.control_level,
            "test_code": self.test_code,
            "expected_value": self.expected_value,
            "observed_value": self.observed_value,
            "status": self.status,
            "reviewed_by": self.reviewed_by,
            "notes": self.notes,
            "performed_at": self.performed_at.isoformat() if self.performed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TechnicianReview(db.Model):
    __tablename__ = "lab_technician_reviews"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    review_code = db.Column(db.String(50), unique=True, nullable=False)
    accession_id = db.Column(
        db.String(36), db.ForeignKey("lab_sample_accessions.id"), nullable=False
    )
    lab_result_id = db.Column(db.String(36), db.ForeignKey("lab_results.id"))
    reviewer = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default="PENDING")
    comments = db.Column(db.Text)
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "review_code": self.review_code,
            "accession_id": self.accession_id,
            "lab_result_id": self.lab_result_id,
            "reviewer": self.reviewer,
            "status": self.status,
            "comments": self.comments,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PathologistReview(db.Model):
    __tablename__ = "lab_pathologist_reviews"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    review_code = db.Column(db.String(50), unique=True, nullable=False)
    accession_id = db.Column(
        db.String(36), db.ForeignKey("lab_sample_accessions.id"), nullable=False
    )
    lab_result_id = db.Column(db.String(36), db.ForeignKey("lab_results.id"))
    pathologist = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default="PENDING")
    diagnosis_notes = db.Column(db.Text)
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "review_code": self.review_code,
            "accession_id": self.accession_id,
            "lab_result_id": self.lab_result_id,
            "pathologist": self.pathologist,
            "status": self.status,
            "diagnosis_notes": self.diagnosis_notes,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CriticalResult(db.Model):
    __tablename__ = "lab_critical_results"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    critical_code = db.Column(db.String(50), unique=True, nullable=False)
    accession_id = db.Column(
        db.String(36), db.ForeignKey("lab_sample_accessions.id"), nullable=False
    )
    test_code = db.Column(db.String(50), nullable=False)
    test_name = db.Column(db.String(255))
    result_value = db.Column(db.String(100))
    critical_type = db.Column(db.String(50), default="HIGH")
    status = db.Column(db.String(50), default="OPEN")
    notified_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "critical_code": self.critical_code,
            "accession_id": self.accession_id,
            "test_code": self.test_code,
            "test_name": self.test_name,
            "result_value": self.result_value,
            "critical_type": self.critical_type,
            "status": self.status,
            "notified_at": self.notified_at.isoformat() if self.notified_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DeltaCheck(db.Model):
    __tablename__ = "lab_delta_checks"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    delta_code = db.Column(db.String(50), unique=True, nullable=False)
    accession_id = db.Column(
        db.String(36), db.ForeignKey("lab_sample_accessions.id"), nullable=False
    )
    test_code = db.Column(db.String(50), nullable=False)
    previous_value = db.Column(db.Float)
    current_value = db.Column(db.Float)
    delta_percent = db.Column(db.Float)
    status = db.Column(db.String(50), default="PENDING")
    reviewed_by = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "delta_code": self.delta_code,
            "accession_id": self.accession_id,
            "test_code": self.test_code,
            "previous_value": self.previous_value,
            "current_value": self.current_value,
            "delta_percent": self.delta_percent,
            "status": self.status,
            "reviewed_by": self.reviewed_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ResultApproval(db.Model):
    __tablename__ = "lab_result_approvals"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    approval_code = db.Column(db.String(50), unique=True, nullable=False)
    accession_id = db.Column(
        db.String(36), db.ForeignKey("lab_sample_accessions.id"), nullable=False
    )
    lab_result_id = db.Column(db.String(36), db.ForeignKey("lab_results.id"))
    approver = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default="PENDING")
    comments = db.Column(db.Text)
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "approval_code": self.approval_code,
            "accession_id": self.accession_id,
            "lab_result_id": self.lab_result_id,
            "approver": self.approver,
            "status": self.status,
            "comments": self.comments,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LabOperationResultRelease(db.Model):
    __tablename__ = "lab_operation_result_releases"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    release_code = db.Column(db.String(50), unique=True, nullable=False)
    accession_id = db.Column(
        db.String(36), db.ForeignKey("lab_sample_accessions.id"), nullable=False
    )
    lab_result_id = db.Column(db.String(36), db.ForeignKey("lab_results.id"))
    released_by = db.Column(db.String(255), default="SYSTEM")
    release_channel = db.Column(db.String(50), default="PATIENT_PORTAL")
    status = db.Column(db.String(50), default="RELEASED")
    released_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "release_code": self.release_code,
            "accession_id": self.accession_id,
            "lab_result_id": self.lab_result_id,
            "released_by": self.released_by,
            "release_channel": self.release_channel,
            "status": self.status,
            "released_at": self.released_at.isoformat() if self.released_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
