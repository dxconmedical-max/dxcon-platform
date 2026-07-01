from datetime import datetime

from app.core.statuses import (
    LAB_ANALYZER_ACTIVE,
    LAB_QUEUE_COMPLETED,
    LAB_QUEUE_QUEUED,
    LAB_QUEUE_RUNNING,
    LAB_WF_ANALYZER_QUEUE,
    LAB_WF_ANALYZER_RUNNING,
    LAB_WORKFLOW_STAGES,
)
from app.extensions.db import db
from app.models.lab_facility import Analyzer, LabBench, LabShift
from app.models.lab_accession import SampleAccession
from app.models.lab_operations import AnalyzerQueue
from app.services.crm_helpers import generate_code, get_or_404, list_resource
from app.services.lab_workflow_service import LabWorkflowError, LabWorkflowService


class AnalyzerService:
    @staticmethod
    def list_analyzers(page=1, per_page=20, status=None, lab_bench_id=None, q=None):
        filters = {"status": status, "lab_bench_id": lab_bench_id, "q": q}
        return list_resource(
            Analyzer,
            lambda item: item.to_dict(),
            search_fields=["analyzer_code", "name", "model", "manufacturer"],
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def create_analyzer(data):
        analyzer = Analyzer(
            analyzer_code=data.get("analyzer_code") or generate_code("ANL"),
            name=data["name"],
            model=data.get("model"),
            manufacturer=data.get("manufacturer"),
            lab_bench_id=data.get("lab_bench_id"),
            status=data.get("status", LAB_ANALYZER_ACTIVE),
            utilization_percent=float(data.get("utilization_percent") or 0),
        )
        db.session.add(analyzer)
        db.session.commit()
        return analyzer

    @staticmethod
    def get_analyzer(analyzer_id):
        return get_or_404(Analyzer, analyzer_id, LabWorkflowError).to_dict()

    @staticmethod
    def update_analyzer(analyzer_id, data):
        analyzer = get_or_404(Analyzer, analyzer_id, LabWorkflowError)
        for field in ("name", "model", "manufacturer", "lab_bench_id", "status"):
            if field in data:
                setattr(analyzer, field, data[field])
        if "utilization_percent" in data:
            analyzer.utilization_percent = float(data["utilization_percent"] or 0)
        analyzer.updated_at = datetime.utcnow()
        db.session.commit()
        return analyzer

    @staticmethod
    def delete_analyzer(analyzer_id):
        analyzer = get_or_404(Analyzer, analyzer_id, LabWorkflowError)
        db.session.delete(analyzer)
        db.session.commit()

    @staticmethod
    def list_queues(page=1, per_page=20, status=None, analyzer_id=None, q=None):
        filters = {"status": status, "analyzer_id": analyzer_id, "q": q}
        return list_resource(
            AnalyzerQueue,
            lambda item: item.to_dict(),
            search_fields=["queue_code"],
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def enqueue_sample(analyzer_id, accession_id, actor="SYSTEM"):
        analyzer = get_or_404(Analyzer, analyzer_id, LabWorkflowError)
        accession = get_or_404(SampleAccession, accession_id, LabWorkflowError)
        position = AnalyzerQueue.query.filter_by(analyzer_id=analyzer.id).count() + 1
        queue = AnalyzerQueue(
            queue_code=generate_code("Q"),
            analyzer_id=analyzer.id,
            accession_id=accession.id,
            position=position,
            status=LAB_QUEUE_QUEUED,
        )
        accession.analyzer_id = analyzer.id
        if LAB_WORKFLOW_STAGES.index(accession.workflow_stage) < LAB_WORKFLOW_STAGES.index(
            LAB_WF_ANALYZER_QUEUE
        ):
            LabWorkflowService.record_transition(
                accession,
                LAB_WF_ANALYZER_QUEUE,
                actor=actor,
                message=f"Queued on analyzer {analyzer.analyzer_code}",
                commit=False,
            )
        db.session.add(queue)
        db.session.commit()
        return queue

    @staticmethod
    def start_queue(queue_id, actor="SYSTEM"):
        queue = get_or_404(AnalyzerQueue, queue_id, LabWorkflowError)
        queue.status = LAB_QUEUE_RUNNING
        queue.started_at = datetime.utcnow()
        accession = get_or_404(SampleAccession, queue.accession_id, LabWorkflowError)
        LabWorkflowService.record_transition(
            accession,
            LAB_WF_ANALYZER_RUNNING,
            actor=actor,
            message="Analyzer run started",
            commit=False,
        )
        analyzer = get_or_404(Analyzer, queue.analyzer_id, LabWorkflowError)
        analyzer.last_run_at = datetime.utcnow()
        analyzer.utilization_percent = min(100, analyzer.utilization_percent + 5)
        db.session.commit()
        return queue

    @staticmethod
    def complete_queue(queue_id, actor="SYSTEM"):
        queue = get_or_404(AnalyzerQueue, queue_id, LabWorkflowError)
        queue.status = LAB_QUEUE_COMPLETED
        queue.completed_at = datetime.utcnow()
        db.session.commit()
        return queue

    @staticmethod
    def get_queue(queue_id):
        return get_or_404(AnalyzerQueue, queue_id, LabWorkflowError).to_dict()

    @staticmethod
    def update_queue(queue_id, data):
        queue = get_or_404(AnalyzerQueue, queue_id, LabWorkflowError)
        if "status" in data:
            queue.status = data["status"]
        if "position" in data:
            queue.position = int(data["position"])
        db.session.commit()
        return queue

    @staticmethod
    def delete_queue(queue_id):
        queue = get_or_404(AnalyzerQueue, queue_id, LabWorkflowError)
        db.session.delete(queue)
        db.session.commit()

    @staticmethod
    def ensure_facility_defaults():
        if not LabBench.query.first():
            bench = LabBench(
                bench_code="BENCH-001",
                name="Hematology Bench",
                department="HEMATOLOGY",
                location="Lab Floor A",
            )
            db.session.add(bench)
            db.session.flush()
            shift = LabShift(
                shift_code="SHIFT-001",
                name="Morning Shift",
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                supervisor="lab.supervisor",
            )
            db.session.add(shift)
            db.session.commit()
        return LabBench.query.first(), LabShift.query.first()
