from datetime import datetime

from app.core.statuses import (
    LAB_ACCESSION_COMPLETED,
    LAB_RELEASE_RELEASED,
    LAB_WF_PATIENT_PORTAL,
    LAB_WF_RELEASE,
)
from app.extensions.db import db
from app.models.lab_accession import SampleAccession
from app.models.lab_operations import LabOperationResultRelease
from app.services.crm_helpers import generate_code, get_or_404, list_resource
from app.services.lab_workflow_service import LabWorkflowError, LabWorkflowService


class ReleaseService:
    @staticmethod
    def list_releases(page=1, per_page=20, status=None, accession_id=None, q=None):
        filters = {"status": status, "accession_id": accession_id, "q": q}
        return list_resource(
            LabOperationResultRelease,
            lambda item: item.to_dict(),
            search_fields=["release_code", "released_by", "release_channel"],
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def create_release(data):
        accession = get_or_404(SampleAccession, data["accession_id"], LabWorkflowError)
        release = LabOperationResultRelease(
            release_code=data.get("release_code") or generate_code("REL"),
            accession_id=accession.id,
            lab_result_id=data.get("lab_result_id"),
            released_by=data.get("released_by", "SYSTEM"),
            release_channel=data.get("release_channel", "PATIENT_PORTAL"),
            status=data.get("status", LAB_RELEASE_RELEASED),
        )
        LabWorkflowService.record_transition(
            accession,
            LAB_WF_RELEASE,
            actor=data.get("released_by", "SYSTEM"),
            message="Result released",
            commit=False,
        )
        LabWorkflowService.record_transition(
            accession,
            LAB_WF_PATIENT_PORTAL,
            actor=data.get("released_by", "SYSTEM"),
            message="Published to patient portal",
            commit=False,
        )
        accession.released_at = datetime.utcnow()
        accession.status = LAB_ACCESSION_COMPLETED
        db.session.add(release)
        db.session.commit()
        return release

    @staticmethod
    def get_release(release_id):
        return get_or_404(LabOperationResultRelease, release_id, LabWorkflowError).to_dict()

    @staticmethod
    def update_release(release_id, data):
        release = get_or_404(LabOperationResultRelease, release_id, LabWorkflowError)
        for field in ("released_by", "release_channel", "status"):
            if field in data:
                setattr(release, field, data[field])
        db.session.commit()
        return release

    @staticmethod
    def delete_release(release_id):
        release = get_or_404(LabOperationResultRelease, release_id, LabWorkflowError)
        db.session.delete(release)
        db.session.commit()
