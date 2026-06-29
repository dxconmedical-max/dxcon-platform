from datetime import datetime

from app.core.pagination import paginate_query, pagination_payload
from app.core.statuses import (
    LAB_ACCESSION_COMPLETED,
    LAB_ACCESSION_IN_PROGRESS,
    LAB_ACCESSION_PENDING,
    LAB_WF_ACCESSION,
    LAB_WF_BOOKING,
    LAB_WF_RECEIVED_LAB,
)
from app.extensions.db import db
from app.models.lab_accession import SampleAccession, Worklist
from app.services.crm_helpers import generate_code, get_or_404, list_resource
from app.services.lab_workflow_service import LabWorkflowError, LabWorkflowService


class AccessionService:
    @staticmethod
    def list_accessions(
        page=1,
        per_page=20,
        status=None,
        workflow_stage=None,
        worklist_id=None,
        analyzer_id=None,
        q=None,
    ):
        filters = {
            "status": status,
            "workflow_stage": workflow_stage,
            "worklist_id": worklist_id,
            "analyzer_id": analyzer_id,
            "q": q,
        }
        return list_resource(
            SampleAccession,
            lambda item: item.to_dict(),
            search_fields=[
                "accession_code",
                "sample_code",
                "patient_name",
                "assigned_technician",
            ],
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def create_accession(data):
        accession = SampleAccession(
            accession_code=data.get("accession_code") or generate_code("ACC"),
            sample_code=data["sample_code"],
            medical_sample_id=data.get("medical_sample_id"),
            medical_order_id=data.get("medical_order_id"),
            patient_name=data.get("patient_name"),
            sample_type=data.get("sample_type", "BLOOD"),
            workflow_stage=data.get("workflow_stage", LAB_WF_BOOKING),
            status=data.get("status", LAB_ACCESSION_PENDING),
            worklist_id=data.get("worklist_id"),
            lab_bench_id=data.get("lab_bench_id"),
            lab_shift_id=data.get("lab_shift_id"),
            analyzer_id=data.get("analyzer_id"),
            priority=data.get("priority", "NORMAL"),
            tat_target_minutes=int(data.get("tat_target_minutes") or 240),
            assigned_technician=data.get("assigned_technician"),
            assigned_pathologist=data.get("assigned_pathologist"),
            notes=data.get("notes"),
        )
        db.session.add(accession)
        db.session.flush()
        LabWorkflowService.record_transition(
            accession,
            accession.workflow_stage,
            actor=data.get("actor", "SYSTEM"),
            message="Accession created",
            commit=False,
        )
        db.session.commit()
        return accession

    @staticmethod
    def get_accession(accession_id):
        accession = get_or_404(SampleAccession, accession_id, LabWorkflowError)
        payload = accession.to_dict()
        payload["transitions"] = [
            t.to_dict() for t in LabWorkflowService.list_transitions(accession_id)
        ]
        return payload

    @staticmethod
    def update_accession(accession_id, data):
        accession = get_or_404(SampleAccession, accession_id, LabWorkflowError)
        for field in (
            "patient_name",
            "sample_type",
            "status",
            "worklist_id",
            "lab_bench_id",
            "lab_shift_id",
            "analyzer_id",
            "priority",
            "assigned_technician",
            "assigned_pathologist",
            "notes",
        ):
            if field in data:
                setattr(accession, field, data[field])
        if "tat_target_minutes" in data:
            accession.tat_target_minutes = int(data["tat_target_minutes"] or 240)
        accession.updated_at = datetime.utcnow()
        db.session.commit()
        return accession

    @staticmethod
    def delete_accession(accession_id):
        accession = get_or_404(SampleAccession, accession_id, LabWorkflowError)
        db.session.delete(accession)
        db.session.commit()

    @staticmethod
    def advance_accession(accession_id, actor="SYSTEM", target_stage=None):
        accession = get_or_404(SampleAccession, accession_id, LabWorkflowError)
        accession.status = LAB_ACCESSION_IN_PROGRESS
        if target_stage:
            transition = LabWorkflowService.record_transition(
                accession,
                target_stage,
                actor=actor,
                message=f"Moved to {target_stage}",
            )
        else:
            transition = LabWorkflowService.advance(
                accession,
                actor=actor,
                message="Workflow advanced",
            )
        if accession.workflow_stage == LAB_WF_RECEIVED_LAB:
            accession.received_at = datetime.utcnow()
        if accession.workflow_stage == LAB_WF_ACCESSION:
            accession.status = LAB_ACCESSION_IN_PROGRESS
        db.session.commit()
        return accession, transition

    @staticmethod
    def receive_at_lab(accession_id, actor="SYSTEM"):
        accession = get_or_404(SampleAccession, accession_id, LabWorkflowError)
        transition = LabWorkflowService.record_transition(
            accession,
            LAB_WF_RECEIVED_LAB,
            actor=actor,
            message="Sample received at laboratory",
        )
        accession.received_at = datetime.utcnow()
        accession.status = LAB_ACCESSION_IN_PROGRESS
        db.session.commit()
        return accession, transition


class WorklistService:
    @staticmethod
    def list_worklists(page=1, per_page=20, status=None, lab_bench_id=None, q=None):
        filters = {"status": status, "lab_bench_id": lab_bench_id, "q": q}
        return list_resource(
            Worklist,
            lambda item: item.to_dict(),
            search_fields=["worklist_code", "name", "assigned_technician"],
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def create_worklist(data):
        worklist = Worklist(
            worklist_code=data.get("worklist_code") or generate_code("WL"),
            name=data["name"],
            lab_bench_id=data.get("lab_bench_id"),
            lab_shift_id=data.get("lab_shift_id"),
            assigned_technician=data.get("assigned_technician"),
            status=data.get("status", "OPEN"),
        )
        db.session.add(worklist)
        db.session.commit()
        return worklist

    @staticmethod
    def get_worklist(worklist_id):
        worklist = get_or_404(Worklist, worklist_id, LabWorkflowError)
        samples = SampleAccession.query.filter_by(worklist_id=worklist.id).all()
        payload = worklist.to_dict()
        payload["samples"] = [sample.to_dict() for sample in samples]
        payload["sample_count"] = len(samples)
        return payload

    @staticmethod
    def update_worklist(worklist_id, data):
        worklist = get_or_404(Worklist, worklist_id, LabWorkflowError)
        for field in ("name", "lab_bench_id", "lab_shift_id", "assigned_technician", "status"):
            if field in data:
                setattr(worklist, field, data[field])
        worklist.updated_at = datetime.utcnow()
        db.session.commit()
        return worklist

    @staticmethod
    def delete_worklist(worklist_id):
        worklist = get_or_404(Worklist, worklist_id, LabWorkflowError)
        db.session.delete(worklist)
        db.session.commit()

    @staticmethod
    def assign_accession(worklist_id, accession_id):
        worklist = get_or_404(Worklist, worklist_id, LabWorkflowError)
        accession = get_or_404(SampleAccession, accession_id, LabWorkflowError)
        accession.worklist_id = worklist.id
        accession.updated_at = datetime.utcnow()
        count = SampleAccession.query.filter_by(worklist_id=worklist.id).count()
        worklist.sample_count = count
        worklist.updated_at = datetime.utcnow()
        db.session.commit()
        return worklist, accession
