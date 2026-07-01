import json
import uuid
from datetime import datetime

from app.core.statuses import (
    FEDERATION_LAB_CONNECTED,
    FEDERATION_LAB_DISCONNECTED,
    FEDERATION_LAB_OFFLINE,
    FEDERATION_LAB_ONLINE,
    FEDERATION_PROVIDER_ACTIVE,
)
from app.extensions.db import db
from app.models.federation_core import (
    FederatedLab,
    FederationCapability,
    FederationEvent,
    FederationProvider,
    FederationProviderBranch,
)


class FederationError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class FederationService:

    @staticmethod
    def _lab_or_raise(lab_id):
        lab = FederatedLab.query.get(lab_id)
        if not lab:
            raise FederationError("Federated lab not found", 404)
        return lab

    @staticmethod
    def _event(lab_id, provider_id, event_type, message, severity="INFO", metadata=None):
        event = FederationEvent(
            event_code=f"FED-{uuid.uuid4().hex[:10].upper()}",
            federated_lab_id=lab_id,
            provider_id=provider_id,
            event_type=event_type,
            message=message,
            severity=severity,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.session.add(event)
        return event

    @staticmethod
    def list_labs(status=None, provider_id=None, page=1, page_size=50):
        query = FederatedLab.query
        if status:
            query = query.filter(FederatedLab.status == status)
        if provider_id:
            query = query.filter(FederatedLab.provider_id == provider_id)
        total = query.count()
        rows = (
            query.order_by(FederatedLab.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "labs": [row.to_dict() for row in rows],
        }

    @staticmethod
    def create_lab(data):
        if not data.get("name"):
            raise FederationError("name is required", 400)
        lab = FederatedLab(
            lab_code=data.get("lab_code") or f"FLAB-{uuid.uuid4().hex[:8].upper()}",
            name=data["name"],
            provider_id=data.get("provider_id"),
            partner_id=data.get("partner_id"),
            city=data.get("city"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            status=data.get("status", FEDERATION_LAB_OFFLINE),
            connection_status=FEDERATION_LAB_DISCONNECTED,
            priority=data.get("priority", 50),
            sla_minutes=data.get("sla_minutes", 240),
            contract_active=data.get("contract_active", True),
            base_price=data.get("base_price", 0),
            metadata_json=json.dumps(data.get("metadata") or {}),
        )
        db.session.add(lab)
        FederationService._event(lab.id, lab.provider_id, "LAB_CREATED", f"Lab {lab.name} registered")
        db.session.commit()
        return lab

    @staticmethod
    def get_lab(lab_id):
        lab = FederationService._lab_or_raise(lab_id)
        payload = lab.to_dict()
        payload["capabilities"] = [
            cap.to_dict()
            for cap in FederationCapability.query.filter_by(
                federated_lab_id=lab.id, is_active=True
            ).all()
        ]
        payload["branches"] = [
            branch.to_dict()
            for branch in FederationProviderBranch.query.filter_by(
                federated_lab_id=lab.id
            ).all()
        ]
        return payload

    @staticmethod
    def connect_lab(lab_id, actor_email="SYSTEM"):
        lab = FederationService._lab_or_raise(lab_id)
        lab.connection_status = FEDERATION_LAB_CONNECTED
        lab.status = FEDERATION_LAB_ONLINE
        lab.connected_at = datetime.utcnow()
        FederationService._event(
            lab.id,
            lab.provider_id,
            "LAB_CONNECTED",
            f"Lab {lab.lab_code} connected",
            metadata={"actor": actor_email},
        )
        db.session.commit()
        return lab

    @staticmethod
    def disconnect_lab(lab_id, actor_email="SYSTEM"):
        lab = FederationService._lab_or_raise(lab_id)
        lab.connection_status = FEDERATION_LAB_DISCONNECTED
        lab.status = FEDERATION_LAB_OFFLINE
        FederationService._event(
            lab.id,
            lab.provider_id,
            "LAB_DISCONNECTED",
            f"Lab {lab.lab_code} disconnected",
            metadata={"actor": actor_email},
        )
        db.session.commit()
        return lab


class FederationProviderService:

    @staticmethod
    def list_providers(page=1, page_size=50, status=None):
        query = FederationProvider.query
        if status:
            query = query.filter(FederationProvider.status == status)
        total = query.count()
        rows = (
            query.order_by(FederationProvider.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "providers": [row.to_dict() for row in rows],
        }

    @staticmethod
    def create_provider(data):
        if not data.get("name"):
            raise FederationError("name is required", 400)
        provider = FederationProvider(
            provider_code=data.get("provider_code") or f"FPRV-{uuid.uuid4().hex[:8].upper()}",
            name=data["name"],
            provider_type=data.get("provider_type", "LAB_NETWORK"),
            contact_email=data.get("contact_email"),
            contact_phone=data.get("contact_phone"),
            status=data.get("status", FEDERATION_PROVIDER_ACTIVE),
            settings_json=json.dumps(data.get("settings") or {}),
        )
        db.session.add(provider)
        db.session.commit()
        return provider

    @staticmethod
    def create_branch(data):
        if not data.get("provider_id") or not data.get("name"):
            raise FederationError("provider_id and name are required", 400)
        branch = FederationProviderBranch(
            branch_code=data.get("branch_code") or f"FBR-{uuid.uuid4().hex[:8].upper()}",
            provider_id=data["provider_id"],
            federated_lab_id=data.get("federated_lab_id"),
            name=data["name"],
            city=data.get("city"),
            address=data.get("address"),
            status=data.get("status", "ACTIVE"),
        )
        db.session.add(branch)
        db.session.commit()
        return branch


class FederationCapabilityService:

    @staticmethod
    def list_capabilities(lab_id=None, test_code=None, page=1, page_size=50):
        query = FederationCapability.query.filter_by(is_active=True)
        if lab_id:
            query = query.filter(FederationCapability.federated_lab_id == lab_id)
        if test_code:
            query = query.filter(FederationCapability.test_code == test_code)
        total = query.count()
        rows = (
            query.order_by(FederationCapability.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "capabilities": [row.to_dict() for row in rows],
        }

    @staticmethod
    def add_capability(data):
        if not data.get("federated_lab_id") or not data.get("test_name"):
            raise FederationError("federated_lab_id and test_name are required", 400)
        FederationService._lab_or_raise(data["federated_lab_id"])
        capability = FederationCapability(
            capability_code=data.get("capability_code") or f"FCAP-{uuid.uuid4().hex[:8].upper()}",
            federated_lab_id=data["federated_lab_id"],
            test_code=data.get("test_code"),
            test_name=data["test_name"],
            modality=data.get("modality", "LAB"),
            turnaround_hours=data.get("turnaround_hours", 24),
        )
        db.session.add(capability)
        db.session.commit()
        return capability

    @staticmethod
    def lab_supports_test(lab_id, test_code):
        if not test_code:
            return True
        return (
            FederationCapability.query.filter_by(
                federated_lab_id=lab_id,
                test_code=test_code,
                is_active=True,
            ).first()
            is not None
        )


class FederationDashboardService:

    @staticmethod
    def get_metrics():
        labs = FederatedLab.query.all()
        online = len([lab for lab in labs if lab.status == FEDERATION_LAB_ONLINE])
        offline = len(labs) - online
        from app.models.federation_capacity import CapacitySnapshot, LabWorkloadSnapshot
        from app.models.federation_failover import FailoverEvent
        from app.models.federation_routing import RoutingDecision

        latest_capacity = CapacitySnapshot.query.order_by(
            CapacitySnapshot.snapshot_date.desc()
        ).all()
        remaining = sum(row.remaining_capacity for row in latest_capacity[:20])
        workload = LabWorkloadSnapshot.query.order_by(
            LabWorkloadSnapshot.snapshot_date.desc()
        ).limit(20).all()
        daily_workload = sum(row.pending_orders + row.in_progress_tests for row in workload)
        avg_tat = (
            sum(row.average_tat_hours for row in workload) / len(workload)
            if workload
            else 0
        )
        qc_rate = (
            sum(row.qc_issue_rate for row in workload) / len(workload)
            if workload
            else 0
        )
        return {
            "labs_online": online,
            "labs_offline": offline,
            "daily_workload": daily_workload,
            "remaining_capacity": remaining,
            "routing_decisions": RoutingDecision.query.count(),
            "failover_events": FailoverEvent.query.count(),
            "sla_compliance": round(100 - qc_rate, 2),
            "average_tat_hours": round(avg_tat, 2),
            "qc_issue_rate": round(qc_rate, 2),
        }
