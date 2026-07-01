from datetime import datetime, timedelta

from sqlalchemy import func

from app.core.statuses import (
    LAB_ACCESSION_PENDING,
    LAB_QC_FAILED,
    LAB_QUEUE_RUNNING,
    LAB_RELEASE_RELEASED,
    LAB_REVIEW_PENDING,
    LAB_WF_ANALYZER_RUNNING,
    LAB_WF_PATHOLOGIST_REVIEW,
    LAB_WF_TECHNICIAN_REVIEW,
)
from app.models.lab_accession import SampleAccession
from app.models.lab_facility import Analyzer
from app.models.lab_operations import (
    CriticalResult,
    LabOperationResultRelease,
    QualityControl,
    TechnicianReview,
)


class LabDashboardService:
    @staticmethod
    def get_dashboard():
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        pending_samples = SampleAccession.query.filter(
            SampleAccession.status.in_([LAB_ACCESSION_PENDING, "IN_PROGRESS"])
        ).count()

        samples_in_analyzer = SampleAccession.query.filter_by(
            workflow_stage=LAB_WF_ANALYZER_RUNNING
        ).count()

        qc_failed = QualityControl.query.filter_by(status=LAB_QC_FAILED).count()

        awaiting_review = SampleAccession.query.filter(
            SampleAccession.workflow_stage.in_(
                [LAB_WF_TECHNICIAN_REVIEW, LAB_WF_PATHOLOGIST_REVIEW]
            )
        ).count()

        critical_results = CriticalResult.query.filter_by(status="OPEN").count()

        released_today = LabOperationResultRelease.query.filter(
            LabOperationResultRelease.released_at >= today_start,
            LabOperationResultRelease.status == LAB_RELEASE_RELEASED,
        ).count()

        completed = SampleAccession.query.filter(
            SampleAccession.released_at.isnot(None),
            SampleAccession.received_at.isnot(None),
        ).all()
        tat_values = []
        sla_met = 0
        for sample in completed:
            if sample.received_at and sample.released_at:
                minutes = (sample.released_at - sample.received_at).total_seconds() / 60
                tat_values.append(minutes)
                if minutes <= (sample.tat_target_minutes or 240):
                    sla_met += 1
        average_tat = round(sum(tat_values) / len(tat_values), 2) if tat_values else 0
        sla_percent = round((sla_met / len(completed)) * 100, 2) if completed else 0

        technician_rows = (
            TechnicianReview.query.with_entities(
                TechnicianReview.reviewer,
                func.count(TechnicianReview.id),
            )
            .group_by(TechnicianReview.reviewer)
            .order_by(func.count(TechnicianReview.id).desc())
            .limit(5)
            .all()
        )
        technician_productivity = [
            {"technician": reviewer, "reviews": count} for reviewer, count in technician_rows
        ]

        analyzers = Analyzer.query.all()
        analyzer_utilization = [
            {
                "analyzer_id": analyzer.id,
                "analyzer_code": analyzer.analyzer_code,
                "utilization_percent": analyzer.utilization_percent,
            }
            for analyzer in analyzers
        ]

        return {
            "pending_samples": pending_samples,
            "samples_in_analyzer": samples_in_analyzer,
            "qc_failed": qc_failed,
            "awaiting_review": awaiting_review,
            "critical_results": critical_results,
            "released_today": released_today,
            "average_tat_minutes": average_tat,
            "sla_percent": sla_percent,
            "technician_productivity": technician_productivity,
            "analyzer_utilization": analyzer_utilization,
            "generated_at": now.isoformat(),
        }
