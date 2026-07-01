from app.extensions.db import db
from app.models.lab_operations import CriticalResult, DeltaCheck
from app.services.crm_helpers import generate_code, get_or_404, list_resource
from app.services.lab_workflow_service import LabWorkflowError


class DeltaCheckService:
    @staticmethod
    def list_delta_checks(page=1, per_page=20, status=None, accession_id=None, q=None):
        filters = {"status": status, "accession_id": accession_id, "q": q}
        return list_resource(
            DeltaCheck,
            lambda item: item.to_dict(),
            search_fields=["delta_code", "test_code", "reviewed_by"],
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def create_delta_check(data):
        previous = float(data.get("previous_value") or 0)
        current = float(data.get("current_value") or 0)
        delta_percent = 0
        if previous:
            delta_percent = abs((current - previous) / previous) * 100
        delta = DeltaCheck(
            delta_code=data.get("delta_code") or generate_code("DLT"),
            accession_id=data["accession_id"],
            test_code=data["test_code"],
            previous_value=previous,
            current_value=current,
            delta_percent=delta_percent,
            status=data.get("status", "PENDING"),
            reviewed_by=data.get("reviewed_by"),
        )
        db.session.add(delta)
        db.session.commit()
        return delta

    @staticmethod
    def get_delta_check(delta_id):
        return get_or_404(DeltaCheck, delta_id, LabWorkflowError).to_dict()

    @staticmethod
    def update_delta_check(delta_id, data):
        delta = get_or_404(DeltaCheck, delta_id, LabWorkflowError)
        for field in ("status", "reviewed_by"):
            if field in data:
                setattr(delta, field, data[field])
        db.session.commit()
        return delta

    @staticmethod
    def delete_delta_check(delta_id):
        delta = get_or_404(DeltaCheck, delta_id, LabWorkflowError)
        db.session.delete(delta)
        db.session.commit()

    @staticmethod
    def accept_delta_check(delta_id, reviewer="SYSTEM"):
        delta = get_or_404(DeltaCheck, delta_id, LabWorkflowError)
        delta.status = "ACCEPTED"
        delta.reviewed_by = reviewer
        db.session.commit()
        return delta


class CriticalResultService:
    @staticmethod
    def list_critical_results(page=1, per_page=20, status=None, accession_id=None, q=None):
        filters = {"status": status, "accession_id": accession_id, "q": q}
        return list_resource(
            CriticalResult,
            lambda item: item.to_dict(),
            search_fields=["critical_code", "test_code", "test_name"],
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def create_critical_result(data):
        critical = CriticalResult(
            critical_code=data.get("critical_code") or generate_code("CRIT"),
            accession_id=data["accession_id"],
            test_code=data["test_code"],
            test_name=data.get("test_name"),
            result_value=data.get("result_value"),
            critical_type=data.get("critical_type", "HIGH"),
            status=data.get("status", "OPEN"),
        )
        db.session.add(critical)
        db.session.commit()
        return critical

    @staticmethod
    def get_critical_result(critical_id):
        return get_or_404(CriticalResult, critical_id, LabWorkflowError).to_dict()

    @staticmethod
    def update_critical_result(critical_id, data):
        critical = get_or_404(CriticalResult, critical_id, LabWorkflowError)
        for field in ("status", "test_name", "result_value", "critical_type"):
            if field in data:
                setattr(critical, field, data[field])
        db.session.commit()
        return critical

    @staticmethod
    def delete_critical_result(critical_id):
        critical = get_or_404(CriticalResult, critical_id, LabWorkflowError)
        db.session.delete(critical)
        db.session.commit()

    @staticmethod
    def notify_critical_result(critical_id):
        from datetime import datetime

        critical = get_or_404(CriticalResult, critical_id, LabWorkflowError)
        critical.status = "NOTIFIED"
        critical.notified_at = datetime.utcnow()
        db.session.commit()
        return critical

    @staticmethod
    def resolve_critical_result(critical_id):
        from datetime import datetime

        critical = get_or_404(CriticalResult, critical_id, LabWorkflowError)
        critical.status = "RESOLVED"
        critical.resolved_at = datetime.utcnow()
        db.session.commit()
        return critical
