from datetime import datetime

from app.core.audit import write_audit
from app.core.events import write_event
from app.core.statuses import SAMPLE_INCIDENT_OPEN, SAMPLE_INCIDENT_RESOLVED
from app.extensions.db import db
from app.models.medical_order import MedicalOrder
from app.models.sample_incident import SampleIncident
from app.services.order_workflow_service import OrderWorkflowService


class IncidentServiceError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class IncidentService:

    @staticmethod
    def _get_order_or_raise(medical_order_id):
        order = MedicalOrder.query.get(medical_order_id)
        if not order:
            raise IncidentServiceError("Medical order not found", 404)
        return order

    @staticmethod
    def log_incident(
        medical_order_id,
        incident_type,
        description,
        sample_id=None,
        severity="MEDIUM",
        reported_by="SYSTEM",
        actor_email="SYSTEM",
        ip_address="",
    ):
        if not incident_type or not description:
            raise IncidentServiceError("incident_type and description are required")

        order = IncidentService._get_order_or_raise(medical_order_id)

        incident = SampleIncident(
            medical_order_id=order.id,
            sample_id=sample_id,
            incident_type=incident_type,
            severity=severity,
            status=SAMPLE_INCIDENT_OPEN,
            description=description,
            reported_by=reported_by,
        )
        db.session.add(incident)
        db.session.flush()

        OrderWorkflowService._write_event(
            order,
            event_type=f"INCIDENT_{incident_type}",
            message=description,
            actor_email=actor_email,
            metadata={"incident_type": incident_type, "severity": severity},
        )

        write_audit(
            action="MEDICAL_ORDER_INCIDENT",
            object_type="SampleIncident",
            object_id=incident.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        write_event(
            event_type="MEDICAL_ORDER_INCIDENT",
            object_type="MedicalOrder",
            object_id=order.id,
            message=description,
        )

        db.session.commit()
        return incident

    @staticmethod
    def list_incidents(medical_order_id):
        IncidentService._get_order_or_raise(medical_order_id)
        return SampleIncident.query.filter_by(
            medical_order_id=medical_order_id
        ).order_by(SampleIncident.created_at.desc()).all()

    @staticmethod
    def resolve_incident(incident_id, resolution_note=None, actor_email="SYSTEM"):
        incident = SampleIncident.query.get(incident_id)
        if not incident:
            raise IncidentServiceError("Incident not found", 404)

        incident.status = SAMPLE_INCIDENT_RESOLVED
        incident.resolution_note = resolution_note
        incident.resolved_at = datetime.utcnow()
        incident.updated_at = datetime.utcnow()
        db.session.commit()
        return incident
