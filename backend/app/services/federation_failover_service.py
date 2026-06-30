import json
import uuid
from datetime import datetime

from app.core.statuses import (
    FAILOVER_TRIGGER_ANALYZER_DOWN,
    FAILOVER_TRIGGER_HOLIDAY,
    FAILOVER_TRIGGER_LAB_OFFLINE,
    FAILOVER_TRIGGER_OVER_CAPACITY,
    FAILOVER_TRIGGER_QC_FAILED,
    FAILOVER_TRIGGER_SLA_TIMEOUT,
)
from app.extensions.db import db
from app.models.federation_capacity import AnalyzerCapacity, CapacityRule, CapacitySnapshot
from app.models.federation_core import FederatedLab
from app.models.federation_failover import FailoverEvent, FailoverRule
from app.services.federation_capacity_service import CapacityCalculatorService
from app.services.federation_service import FederationError, FederationService


class FailoverService:

    TRIGGER_TYPES = [
        FAILOVER_TRIGGER_LAB_OFFLINE,
        FAILOVER_TRIGGER_ANALYZER_DOWN,
        FAILOVER_TRIGGER_QC_FAILED,
        FAILOVER_TRIGGER_HOLIDAY,
        FAILOVER_TRIGGER_OVER_CAPACITY,
        FAILOVER_TRIGGER_SLA_TIMEOUT,
    ]

    @staticmethod
    def _find_fallback(source_lab_id):
        rule = FailoverRule.query.filter_by(
            target_lab_id=source_lab_id, is_active=True
        ).first()
        if rule and rule.fallback_lab_id:
            return FederatedLab.query.get(rule.fallback_lab_id)
        fallback = (
            FederatedLab.query.filter(
                FederatedLab.id != source_lab_id,
                FederatedLab.status == "ONLINE",
            )
            .order_by(FederatedLab.priority.desc())
            .first()
        )
        return fallback

    @staticmethod
    def _create_event(trigger_type, source_lab, fallback_lab, message, metadata=None):
        event = FailoverEvent(
            event_code=f"FO-{uuid.uuid4().hex[:10].upper()}",
            trigger_type=trigger_type,
            source_lab_id=source_lab.id if source_lab else None,
            fallback_lab_id=fallback_lab.id if fallback_lab else None,
            status="TRIGGERED",
            message=message,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.session.add(event)
        return event

    @staticmethod
    def check(data):
        lab_id = data.get("federated_lab_id") or data.get("lab_id")
        if not lab_id:
            raise FederationError("federated_lab_id is required", 400)
        lab = FederationService._lab_or_raise(lab_id)
        triggered = []

        if lab.status != "ONLINE" or lab.connection_status != "CONNECTED":
            fallback = FailoverService._find_fallback(lab.id)
            triggered.append(
                FailoverService._create_event(
                    FAILOVER_TRIGGER_LAB_OFFLINE,
                    lab,
                    fallback,
                    f"Lab {lab.lab_code} offline; failover to {fallback.lab_code if fallback else 'none'}",
                )
            )

        analyzers = AnalyzerCapacity.query.filter_by(federated_lab_id=lab.id).all()
        down_analyzers = [a for a in analyzers if a.status != "ONLINE"]
        if down_analyzers:
            fallback = FailoverService._find_fallback(lab.id)
            triggered.append(
                FailoverService._create_event(
                    FAILOVER_TRIGGER_ANALYZER_DOWN,
                    lab,
                    fallback,
                    f"{len(down_analyzers)} analyzer(s) down",
                    metadata={"analyzer_codes": [a.analyzer_code for a in down_analyzers]},
                )
            )

        failed_qc = [a for a in analyzers if a.qc_status != "PASS"]
        if failed_qc:
            fallback = FailoverService._find_fallback(lab.id)
            triggered.append(
                FailoverService._create_event(
                    FAILOVER_TRIGGER_QC_FAILED,
                    lab,
                    fallback,
                    f"QC failed on {len(failed_qc)} analyzer(s)",
                )
            )

        if data.get("holiday_mode"):
            fallback = FailoverService._find_fallback(lab.id)
            triggered.append(
                FailoverService._create_event(
                    FAILOVER_TRIGGER_HOLIDAY,
                    lab,
                    fallback,
                    f"Lab {lab.lab_code} closed for holiday",
                )
            )

        calc = CapacityCalculatorService.calculate_for_lab(lab.id)
        if calc.get("blocked"):
            fallback = FailoverService._find_fallback(lab.id)
            triggered.append(
                FailoverService._create_event(
                    FAILOVER_TRIGGER_OVER_CAPACITY,
                    lab,
                    fallback,
                    f"Lab {lab.lab_code} over capacity",
                    metadata=calc,
                )
            )

        if data.get("sla_timeout"):
            fallback = FailoverService._find_fallback(lab.id)
            triggered.append(
                FailoverService._create_event(
                    FAILOVER_TRIGGER_SLA_TIMEOUT,
                    lab,
                    fallback,
                    f"SLA timeout for lab {lab.lab_code}",
                )
            )

        db.session.commit()
        return {
            "lab_id": lab.id,
            "lab_code": lab.lab_code,
            "checks_run": len(FailoverService.TRIGGER_TYPES),
            "events_triggered": len(triggered),
            "events": [event.to_dict() for event in triggered],
        }

    @staticmethod
    def list_events(page=1, page_size=50, trigger_type=None):
        query = FailoverEvent.query
        if trigger_type:
            query = query.filter(FailoverEvent.trigger_type == trigger_type)
        total = query.count()
        rows = (
            query.order_by(FailoverEvent.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "events": [row.to_dict() for row in rows],
        }
