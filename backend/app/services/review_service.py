from datetime import datetime

from app.core.statuses import (
    LAB_APPROVAL_APPROVED,
    LAB_APPROVAL_PENDING,
    LAB_REVIEW_APPROVED,
    LAB_REVIEW_PENDING,
    LAB_WF_PATHOLOGIST_REVIEW,
    LAB_WF_TECHNICIAN_REVIEW,
    LAB_WORKFLOW_STAGES,
)
from app.extensions.db import db
from app.models.lab_accession import SampleAccession
from app.models.lab_operations import PathologistReview, ResultApproval, TechnicianReview
from app.services.crm_helpers import generate_code, get_or_404, list_resource
from app.services.lab_workflow_service import LabWorkflowError, LabWorkflowService


class ReviewService:
    @staticmethod
    def list_reviews(page=1, per_page=20, review_type=None, status=None, accession_id=None, q=None):
        if review_type == "pathologist":
            model = PathologistReview
            search_fields = ["review_code", "pathologist"]
        elif review_type == "approval":
            model = ResultApproval
            search_fields = ["approval_code", "approver"]
        else:
            model = TechnicianReview
            search_fields = ["review_code", "reviewer"]

        filters = {"status": status, "accession_id": accession_id, "q": q}
        return list_resource(
            model,
            lambda item: item.to_dict(),
            search_fields=search_fields,
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def create_technician_review(data):
        review = TechnicianReview(
            review_code=data.get("review_code") or generate_code("TR"),
            accession_id=data["accession_id"],
            lab_result_id=data.get("lab_result_id"),
            reviewer=data["reviewer"],
            status=data.get("status", LAB_REVIEW_PENDING),
            comments=data.get("comments"),
        )
        accession = get_or_404(SampleAccession, data["accession_id"], LabWorkflowError)
        if LAB_WORKFLOW_STAGES.index(accession.workflow_stage) < LAB_WORKFLOW_STAGES.index(
            LAB_WF_TECHNICIAN_REVIEW
        ):
            LabWorkflowService.record_transition(
                accession,
                LAB_WF_TECHNICIAN_REVIEW,
                actor=data["reviewer"],
                message="Technician review created",
                commit=False,
            )
        db.session.add(review)
        db.session.commit()
        return review

    @staticmethod
    def create_pathologist_review(data):
        review = PathologistReview(
            review_code=data.get("review_code") or generate_code("PR"),
            accession_id=data["accession_id"],
            lab_result_id=data.get("lab_result_id"),
            pathologist=data["pathologist"],
            status=data.get("status", LAB_REVIEW_PENDING),
            diagnosis_notes=data.get("diagnosis_notes"),
        )
        accession = get_or_404(SampleAccession, data["accession_id"], LabWorkflowError)
        if LAB_WORKFLOW_STAGES.index(accession.workflow_stage) < LAB_WORKFLOW_STAGES.index(
            LAB_WF_PATHOLOGIST_REVIEW
        ):
            LabWorkflowService.record_transition(
                accession,
                LAB_WF_PATHOLOGIST_REVIEW,
                actor=data["pathologist"],
                message="Pathologist review created",
                commit=False,
            )
        db.session.add(review)
        db.session.commit()
        return review

    @staticmethod
    def create_approval(data):
        approval = ResultApproval(
            approval_code=data.get("approval_code") or generate_code("APR"),
            accession_id=data["accession_id"],
            lab_result_id=data.get("lab_result_id"),
            approver=data["approver"],
            status=data.get("status", LAB_APPROVAL_PENDING),
            comments=data.get("comments"),
        )
        db.session.add(approval)
        db.session.commit()
        return approval

    @staticmethod
    def get_review(review_id, review_type="technician"):
        if review_type == "pathologist":
            return get_or_404(PathologistReview, review_id, LabWorkflowError).to_dict()
        if review_type == "approval":
            return get_or_404(ResultApproval, review_id, LabWorkflowError).to_dict()
        return get_or_404(TechnicianReview, review_id, LabWorkflowError).to_dict()

    @staticmethod
    def approve_technician_review(review_id, actor="SYSTEM"):
        review = get_or_404(TechnicianReview, review_id, LabWorkflowError)
        review.status = LAB_REVIEW_APPROVED
        review.reviewed_at = datetime.utcnow()
        db.session.commit()
        return review

    @staticmethod
    def approve_pathologist_review(review_id, actor="SYSTEM"):
        review = get_or_404(PathologistReview, review_id, LabWorkflowError)
        review.status = LAB_REVIEW_APPROVED
        review.reviewed_at = datetime.utcnow()
        db.session.commit()
        return review

    @staticmethod
    def approve_result(approval_id, actor="SYSTEM"):
        approval = get_or_404(ResultApproval, approval_id, LabWorkflowError)
        approval.status = LAB_APPROVAL_APPROVED
        approval.approved_at = datetime.utcnow()
        db.session.commit()
        return approval

    @staticmethod
    def delete_review(review_id, review_type="technician"):
        if review_type == "pathologist":
            review = get_or_404(PathologistReview, review_id, LabWorkflowError)
        elif review_type == "approval":
            review = get_or_404(ResultApproval, review_id, LabWorkflowError)
        else:
            review = get_or_404(TechnicianReview, review_id, LabWorkflowError)
        db.session.delete(review)
        db.session.commit()
