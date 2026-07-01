import json
from datetime import datetime

from app.events.domain_event import DomainEvent
from app.events.event_registry import EventRegistry
from app.extensions.db import db
from app.models.integration_platform import IntegrationDomainEvent, IntegrationEventDeliveryLog


class EventBus:
    @classmethod
    def publish(cls, event: DomainEvent):
        row = IntegrationDomainEvent(
            id=event.event_id,
            event_code=f"EVT-{event.event_id[:8].upper()}",
            event_type=event.event_type,
            source=event.source,
            correlation_id=event.correlation_id,
            payload_json=json.dumps(event.payload),
            status="PUBLISHED",
            published_at=datetime.utcnow(),
        )
        db.session.add(row)
        deliveries = []
        for handler in EventRegistry.handlers_for(event.event_type):
            try:
                result = handler(event)
                deliveries.append({"handler": getattr(handler, "__name__", "handler"), "status": "OK", "result": result})
            except Exception as exc:
                deliveries.append({"handler": getattr(handler, "__name__", "handler"), "status": "FAILED", "error": str(exc)})
        for delivery in deliveries:
            db.session.add(
                IntegrationEventDeliveryLog(
                    event_id=event.event_id,
                    handler_name=delivery["handler"],
                    status=delivery["status"],
                    detail_json=json.dumps(delivery),
                )
            )
        db.session.commit()
        return {"event": event.to_dict(), "deliveries": deliveries}

    @classmethod
    def subscribe(cls, event_type: str, handler):
        EventRegistry.register_handler(event_type, handler)
        return {"event_type": event_type, "handler": getattr(handler, "__name__", "handler")}
