import json
import uuid
from datetime import datetime, timedelta

from app.extensions.db import db
from app.models.federation_capacity import (
    AnalyzerCapacity,
    CapacityRule,
    CapacitySnapshot,
    LabWorkloadSnapshot,
)
from app.models.federation_core import FederatedLab
from app.services.federation_service import FederationError, FederationService


class CapacityCalculatorService:

    @staticmethod
    def calculate_for_lab(lab_id, pending_orders=0):
        lab = FederationService._lab_or_raise(lab_id)
        rule = CapacityRule.query.filter_by(federated_lab_id=lab_id, is_active=True).first()
        max_daily = rule.max_daily_tests if rule else 500

        analyzers = AnalyzerCapacity.query.filter_by(federated_lab_id=lab_id).all()
        analyzer_capacity = sum(
            analyzer.hourly_throughput * 8
            for analyzer in analyzers
            if analyzer.status == "ONLINE" and analyzer.qc_status == "PASS"
        )
        total_capacity = max(max_daily, analyzer_capacity or max_daily)

        latest = (
            CapacitySnapshot.query.filter_by(federated_lab_id=lab_id)
            .order_by(CapacitySnapshot.snapshot_date.desc())
            .first()
        )
        used_capacity = pending_orders
        if latest:
            used_capacity = max(latest.used_capacity, pending_orders)
        remaining = max(total_capacity - used_capacity, 0)
        utilization = round((used_capacity / total_capacity) * 100, 2) if total_capacity else 0

        return {
            "federated_lab_id": lab_id,
            "lab_code": lab.lab_code,
            "total_capacity": total_capacity,
            "used_capacity": used_capacity,
            "remaining_capacity": remaining,
            "utilization_rate": utilization,
            "analyzer_count": len(analyzers),
            "blocked": rule and utilization >= (rule.block_threshold * 100) if rule else False,
        }


class CapacityService:

    @staticmethod
    def get_capacity(lab_id=None):
        if lab_id:
            return CapacityCalculatorService.calculate_for_lab(lab_id)
        labs = FederatedLab.query.all()
        rows = [CapacityCalculatorService.calculate_for_lab(lab.id) for lab in labs]
        return {
            "labs_total": len(rows),
            "total_capacity": sum(row["total_capacity"] for row in rows),
            "remaining_capacity": sum(row["remaining_capacity"] for row in rows),
            "labs": rows,
        }

    @staticmethod
    def update_capacity(data):
        lab_id = data.get("federated_lab_id")
        if not lab_id:
            raise FederationError("federated_lab_id is required", 400)
        FederationService._lab_or_raise(lab_id)
        calc = CapacityCalculatorService.calculate_for_lab(
            lab_id,
            pending_orders=data.get("used_capacity", 0),
        )
        snapshot = CapacitySnapshot(
            snapshot_code=f"FCAP-{uuid.uuid4().hex[:10].upper()}",
            federated_lab_id=lab_id,
            snapshot_date=datetime.utcnow(),
            total_capacity=calc["total_capacity"],
            used_capacity=calc["used_capacity"],
            remaining_capacity=calc["remaining_capacity"],
            utilization_rate=calc["utilization_rate"],
            metrics_json=json.dumps(calc),
        )
        db.session.add(snapshot)
        workload = LabWorkloadSnapshot(
            snapshot_code=f"FWL-{uuid.uuid4().hex[:10].upper()}",
            federated_lab_id=lab_id,
            snapshot_date=datetime.utcnow(),
            pending_orders=data.get("pending_orders", calc["used_capacity"]),
            in_progress_tests=data.get("in_progress_tests", 0),
            completed_tests=data.get("completed_tests", 0),
            average_tat_hours=data.get("average_tat_hours", 24),
            qc_issue_rate=data.get("qc_issue_rate", 0),
        )
        db.session.add(workload)
        db.session.commit()
        return {"snapshot": snapshot.to_dict(), "workload": workload.to_dict(), "calculation": calc}

    @staticmethod
    def history(lab_id=None, days=7, page=1, page_size=50):
        start = datetime.utcnow() - timedelta(days=days)
        query = CapacitySnapshot.query.filter(CapacitySnapshot.snapshot_date >= start)
        if lab_id:
            query = query.filter(CapacitySnapshot.federated_lab_id == lab_id)
        total = query.count()
        rows = (
            query.order_by(CapacitySnapshot.snapshot_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "snapshots": [row.to_dict() for row in rows],
        }
