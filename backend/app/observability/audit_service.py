import json
import uuid

from app.extensions.db import db
from app.models.observability_platform import AuditActor, AuditEvent, AuditResource, AuditTimeline
from app.observability.logging_service import StructuredLoggingService
from app.core.request_context import get_request_id
from app.observability.trace_service import TraceService


AUDIT_EVENT_TYPES = (
    "Login",
    "Logout",
    "Patient",
    "Order",
    "Sample",
    "Result",
    "Invoice",
    "Partner",
    "Integration",
    "Notification",
    "API key",
)


class AuditTimelineService:
    @staticmethod
    def ensure_default_timeline():
        row = AuditTimeline.query.filter_by(timeline_code="OBS-DEFAULT").first()
        if row:
            return row
        row = AuditTimeline(timeline_code="OBS-DEFAULT", name="Platform Audit Timeline")
        db.session.add(row)
        db.session.commit()
        return row

    @staticmethod
    def record(event_type, action, actor=None, resource=None, module="observability", detail=None):
        timeline = AuditTimelineService.ensure_default_timeline()
        actor_row = AuditTimelineService._resolve_actor(actor)
        resource_row = AuditTimelineService._resolve_resource(resource, event_type)
        context = TraceService.current_context()
        event = AuditEvent(
            event_code=f"AUD-{uuid.uuid4().hex[:8].upper()}",
            timeline_id=timeline.id,
            actor_id=actor_row.id if actor_row else None,
            resource_id=resource_row.id if resource_row else None,
            event_type=event_type,
            action=action,
            module=module,
            request_id=get_request_id(),
            trace_id=context.get("trace_id"),
            detail_json=json.dumps(detail or {}),
        )
        db.session.add(event)
        db.session.commit()
        StructuredLoggingService.log_event(
            module,
            f"audit:{event_type}:{action}",
            extra={"event_code": event.event_code, "detail": detail or {}},
        )
        return event.to_dict()

    @staticmethod
    def _resolve_actor(actor):
        if not actor:
            return None
        code = actor.get("actor_code") or f"ACT-{uuid.uuid4().hex[:8].upper()}"
        row = AuditActor.query.filter_by(actor_code=code).first()
        if row:
            return row
        row = AuditActor(
            actor_code=code,
            actor_type=actor.get("actor_type") or "USER",
            display_name=actor.get("display_name") or "System",
            user_id=actor.get("user_id"),
        )
        db.session.add(row)
        db.session.commit()
        return row

    @staticmethod
    def _resolve_resource(resource, default_type):
        if not resource:
            return None
        code = resource.get("resource_code") or f"RES-{uuid.uuid4().hex[:8].upper()}"
        row = AuditResource.query.filter_by(resource_code=code).first()
        if row:
            return row
        row = AuditResource(
            resource_code=code,
            resource_type=resource.get("resource_type") or default_type,
            resource_id=resource.get("resource_id") or code,
            display_name=resource.get("display_name"),
        )
        db.session.add(row)
        db.session.commit()
        return row

    @staticmethod
    def list_events(limit=100, event_type=None):
        query = AuditEvent.query
        if event_type:
            query = query.filter_by(event_type=event_type)
        rows = query.order_by(AuditEvent.created_at.desc()).limit(limit).all()
        return {"count": len(rows), "events": [row.to_dict() for row in rows], "event_types": AUDIT_EVENT_TYPES}

    @staticmethod
    def list_timelines():
        rows = AuditTimeline.query.order_by(AuditTimeline.created_at.desc()).all()
        return {"count": len(rows), "timelines": [row.to_dict() for row in rows]}
