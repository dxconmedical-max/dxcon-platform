import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app
from app.core.statuses import LAB_WORKFLOW_STAGES, LAB_WF_BOOKING
from app.extensions.db import db
from app.models.lab_accession import SampleAccession
from app.models.lab_facility import Analyzer, LabBench, LabShift
from app.models.lab_operations import (
    AnalyzerQueue,
    CriticalResult,
    PathologistReview,
    QualityControl,
    TechnicianReview,
)
from app.services.analyzer_service import AnalyzerService
from app.services.lab_workflow_service import LabWorkflowService
from app.services.qc_service import QCService
from app.services.release_service import ReleaseService
from app.services.review_service import ReviewService


SAMPLE_TYPES = ["BLOOD", "SERUM", "URINE", "PLASMA"]
TECHNICIANS = ["tech.alpha", "tech.beta", "tech.gamma", "tech.delta"]
PATHOLOGISTS = ["path.one", "path.two", "path.three"]
TESTS = ["GLU", "CBC", "HBA1C", "TSH", "CRP"]


def seed_lab_operations_demo(force=False):
    if not force and SampleAccession.query.count() >= 200:
        return {
            "samples": SampleAccession.query.count(),
            "analyzers": Analyzer.query.count(),
            "qc_records": QualityControl.query.count(),
            "critical_results": CriticalResult.query.count(),
            "reviews": TechnicianReview.query.count() + PathologistReview.query.count(),
            "skipped": True,
        }

    bench = LabBench(
        bench_code="BENCH-001",
        name="Core Lab Bench",
        department="CORE",
        location="Floor 2",
    )
    db.session.add(bench)
    db.session.flush()

    shift = LabShift(
        shift_code="SHIFT-001",
        name="Day Shift",
        start_time=datetime.utcnow() - timedelta(hours=2),
        end_time=datetime.utcnow() + timedelta(hours=6),
        supervisor="lab.supervisor",
    )
    db.session.add(shift)
    db.session.flush()

    analyzers = []
    for idx in range(10):
        analyzer = Analyzer(
            analyzer_code=f"ANL-{idx + 1:03d}",
            name=f"Analyzer {idx + 1}",
            model=f"DX-{100 + idx}",
            manufacturer="DxCon Instruments",
            lab_bench_id=bench.id,
            status="ACTIVE",
            utilization_percent=random.uniform(10, 85),
        )
        db.session.add(analyzer)
        analyzers.append(analyzer)
    db.session.flush()

    accessions = []
    for idx in range(200):
        stage = random.choice(LAB_WORKFLOW_STAGES)
        accession = SampleAccession(
            accession_code=f"ACC-{idx + 1:04d}",
            sample_code=f"SMP-{idx + 1:05d}",
            patient_name=f"Patient {idx + 1}",
            sample_type=random.choice(SAMPLE_TYPES),
            workflow_stage=LAB_WF_BOOKING,
            status="PENDING" if stage != "PATIENT_PORTAL" else "COMPLETED",
            lab_bench_id=bench.id,
            lab_shift_id=shift.id,
            analyzer_id=random.choice(analyzers).id if idx % 3 == 0 else None,
            priority=random.choice(["NORMAL", "URGENT", "STAT"]),
            tat_target_minutes=random.choice([120, 180, 240, 360]),
            assigned_technician=random.choice(TECHNICIANS),
            assigned_pathologist=random.choice(PATHOLOGISTS),
        )
        db.session.add(accession)
        db.session.flush()
        LabWorkflowService.record_transition(
            accession,
            LAB_WF_BOOKING,
            actor="seed",
            message="Booking created",
            commit=False,
        )
        target_index = LAB_WORKFLOW_STAGES.index(stage)
        for step in LAB_WORKFLOW_STAGES[1 : target_index + 1]:
            LabWorkflowService.record_transition(
                accession,
                step,
                actor="seed",
                message=f"Auto transition to {step}",
                commit=False,
            )
        if accession.workflow_stage in ("RECEIVED_LAB", "ACCESSION", "ANALYZER_QUEUE", "ANALYZER_RUNNING", "QC", "TECHNICIAN_REVIEW", "PATHOLOGIST_REVIEW", "RELEASE", "PATIENT_PORTAL"):
            accession.received_at = datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        if accession.workflow_stage == "PATIENT_PORTAL":
            accession.released_at = datetime.utcnow() - timedelta(hours=random.randint(0, 12))
            accession.status = "COMPLETED"
        accessions.append(accession)
    db.session.flush()

    for idx, accession in enumerate(accessions[:80]):
        if accession.workflow_stage in ("ANALYZER_QUEUE", "ANALYZER_RUNNING", "QC", "TECHNICIAN_REVIEW", "PATHOLOGIST_REVIEW", "RELEASE", "PATIENT_PORTAL"):
            analyzer = analyzers[idx % len(analyzers)]
            queue = AnalyzerQueue(
                queue_code=f"Q-{idx + 1:04d}",
                analyzer_id=analyzer.id,
                accession_id=accession.id,
                position=idx + 1,
                status=random.choice(["QUEUED", "RUNNING", "COMPLETED"]),
                queued_at=datetime.utcnow() - timedelta(hours=2),
            )
            db.session.add(queue)

    for idx in range(50):
        accession = accessions[idx]
        qc = QualityControl(
            qc_code=f"QC-{idx + 1:04d}",
            accession_id=accession.id,
            analyzer_id=accession.analyzer_id or analyzers[idx % len(analyzers)].id,
            control_level=random.choice(["LEVEL_1", "LEVEL_2"]),
            test_code=random.choice(TESTS),
            expected_value=random.uniform(50, 100),
            observed_value=random.uniform(48, 102),
            status=random.choice(["PENDING", "PASSED", "FAILED"]),
            reviewed_by=random.choice(TECHNICIANS),
        )
        db.session.add(qc)

    for idx in range(20):
        accession = accessions[idx + 10]
        critical = CriticalResult(
            critical_code=f"CRIT-{idx + 1:04d}",
            accession_id=accession.id,
            test_code=random.choice(TESTS),
            test_name=f"Critical {random.choice(TESTS)}",
            result_value=str(random.uniform(200, 500)),
            critical_type=random.choice(["HIGH", "LOW"]),
            status=random.choice(["OPEN", "NOTIFIED", "RESOLVED"]),
        )
        db.session.add(critical)

    review_count = 0
    for idx in range(20):
        accession = accessions[idx + 30]
        ReviewService.create_technician_review(
            {
                "accession_id": accession.id,
                "reviewer": random.choice(TECHNICIANS),
                "comments": f"Technician review {idx + 1}",
            }
        )
        review_count += 1

    for idx in range(10):
        accession = accessions[idx + 60]
        ReviewService.create_pathologist_review(
            {
                "accession_id": accession.id,
                "pathologist": random.choice(PATHOLOGISTS),
                "diagnosis_notes": f"Pathologist review {idx + 1}",
            }
        )
        review_count += 1

    for accession in accessions:
        if accession.workflow_stage == "RELEASE":
            ReleaseService.create_release(
                {
                    "accession_id": accession.id,
                    "released_by": "seed",
                    "release_channel": "PATIENT_PORTAL",
                }
            )

    db.session.commit()
    return {
        "samples": SampleAccession.query.count(),
        "analyzers": Analyzer.query.count(),
        "qc_records": QualityControl.query.count(),
        "critical_results": CriticalResult.query.count(),
        "reviews": TechnicianReview.query.count() + PathologistReview.query.count(),
        "skipped": False,
    }


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        summary = seed_lab_operations_demo(force="--force" in sys.argv)
        print(summary)
