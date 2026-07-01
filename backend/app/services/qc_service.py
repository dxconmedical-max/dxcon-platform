from datetime import datetime

from app.core.statuses import LAB_QC_FAILED, LAB_QC_PASSED, LAB_QC_PENDING, LAB_WF_QC, LAB_WORKFLOW_STAGES
from app.extensions.db import db
from app.models.lab_accession import SampleAccession
from app.models.lab_operations import QualityControl
from app.services.crm_helpers import generate_code, get_or_404, list_resource
from app.services.lab_workflow_service import LabWorkflowError, LabWorkflowService


class QCService:
    @staticmethod
    def list_qc(page=1, per_page=20, status=None, analyzer_id=None, accession_id=None, q=None):
        filters = {
            "status": status,
            "analyzer_id": analyzer_id,
            "accession_id": accession_id,
            "q": q,
        }
        return list_resource(
            QualityControl,
            lambda item: item.to_dict(),
            search_fields=["qc_code", "test_code", "reviewed_by"],
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def create_qc(data):
        qc = QualityControl(
            qc_code=data.get("qc_code") or generate_code("QC"),
            accession_id=data.get("accession_id"),
            analyzer_id=data.get("analyzer_id"),
            control_level=data.get("control_level", "LEVEL_1"),
            test_code=data.get("test_code"),
            expected_value=float(data.get("expected_value") or 0),
            observed_value=float(data.get("observed_value") or 0),
            status=data.get("status", LAB_QC_PENDING),
            reviewed_by=data.get("reviewed_by"),
            notes=data.get("notes"),
        )
        db.session.add(qc)
        if qc.accession_id:
            accession = SampleAccession.query.get(qc.accession_id)
            if accession and LAB_WORKFLOW_STAGES.index(
                accession.workflow_stage
            ) < LAB_WORKFLOW_STAGES.index(LAB_WF_QC):
                LabWorkflowService.record_transition(
                    accession,
                    LAB_WF_QC,
                    actor=data.get("reviewed_by", "SYSTEM"),
                    message="QC record created",
                    commit=False,
                )
        db.session.commit()
        return qc

    @staticmethod
    def get_qc(qc_id):
        return get_or_404(QualityControl, qc_id, LabWorkflowError).to_dict()

    @staticmethod
    def update_qc(qc_id, data):
        qc = get_or_404(QualityControl, qc_id, LabWorkflowError)
        for field in (
            "control_level",
            "test_code",
            "status",
            "reviewed_by",
            "notes",
        ):
            if field in data:
                setattr(qc, field, data[field])
        for field in ("expected_value", "observed_value"):
            if field in data:
                setattr(qc, field, float(data[field] or 0))
        db.session.commit()
        return qc

    @staticmethod
    def delete_qc(qc_id):
        qc = get_or_404(QualityControl, qc_id, LabWorkflowError)
        db.session.delete(qc)
        db.session.commit()

    @staticmethod
    def evaluate_qc(qc_id, actor="SYSTEM"):
        qc = get_or_404(QualityControl, qc_id, LabWorkflowError)
        tolerance = abs(qc.expected_value or 0) * 0.05 or 1
        delta = abs((qc.observed_value or 0) - (qc.expected_value or 0))
        qc.status = LAB_QC_PASSED if delta <= tolerance else LAB_QC_FAILED
        qc.reviewed_by = actor
        qc.performed_at = datetime.utcnow()
        db.session.commit()
        return qc
