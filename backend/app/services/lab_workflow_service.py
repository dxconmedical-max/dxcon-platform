import json
from datetime import datetime

from app.core.statuses import LAB_WORKFLOW_STAGES
from app.extensions.db import db
from app.models.lab_accession import LabWorkflowTransition, SampleAccession


class LabWorkflowError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class LabWorkflowService:
    @staticmethod
    def next_stage(current_stage):
        if current_stage not in LAB_WORKFLOW_STAGES:
            return LAB_WORKFLOW_STAGES[0]
        idx = LAB_WORKFLOW_STAGES.index(current_stage)
        if idx >= len(LAB_WORKFLOW_STAGES) - 1:
            return current_stage
        return LAB_WORKFLOW_STAGES[idx + 1]

    @staticmethod
    def can_transition(from_stage, to_stage):
        if from_stage not in LAB_WORKFLOW_STAGES or to_stage not in LAB_WORKFLOW_STAGES:
            return False
        return LAB_WORKFLOW_STAGES.index(to_stage) >= LAB_WORKFLOW_STAGES.index(from_stage)

    @staticmethod
    def record_transition(
        accession,
        to_stage,
        actor="SYSTEM",
        message=None,
        metadata=None,
        commit=True,
    ):
        from_stage = accession.workflow_stage
        if not LabWorkflowService.can_transition(from_stage, to_stage):
            raise LabWorkflowError(
                f"Cannot transition from {from_stage} to {to_stage}",
                409,
            )
        transition = LabWorkflowTransition(
            accession_id=accession.id,
            from_stage=from_stage,
            to_stage=to_stage,
            actor=actor,
            message=message,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        accession.workflow_stage = to_stage
        accession.updated_at = datetime.utcnow()
        db.session.add(transition)
        if commit:
            db.session.commit()
        return transition

    @staticmethod
    def advance(accession, actor="SYSTEM", message=None, metadata=None):
        next_stage = LabWorkflowService.next_stage(accession.workflow_stage)
        return LabWorkflowService.record_transition(
            accession,
            next_stage,
            actor=actor,
            message=message,
            metadata=metadata,
        )

    @staticmethod
    def list_transitions(accession_id):
        return (
            LabWorkflowTransition.query.filter_by(accession_id=accession_id)
            .order_by(LabWorkflowTransition.created_at.asc())
            .all()
        )

    @staticmethod
    def run_full_workflow(accession, actor="SYSTEM"):
        transitions = []
        while accession.workflow_stage != LAB_WORKFLOW_STAGES[-1]:
            transition = LabWorkflowService.advance(accession, actor=actor)
            transitions.append(transition)
            if accession.workflow_stage == "RECEIVED_LAB":
                accession.received_at = datetime.utcnow()
            if accession.workflow_stage == "RELEASE":
                accession.released_at = datetime.utcnow()
        accession.status = "COMPLETED"
        db.session.commit()
        return transitions
