from datetime import datetime

from app.extensions.db import db
from app.models.shipment import Shipment
from app.models.shipment_timeline import ShipmentTimeline
from app.models.transport_box import TransportBox
from app.core.audit import write_audit
from app.core.events import write_event
from app.core.statuses import (
    BOX_IN_TRANSIT,
    BOX_IN_USE,
    BOX_ONLINE,
    SHIPMENT_ACCEPTED,
    SHIPMENT_CREATED,
    SHIPMENT_IN_TRANSIT,
)

GPS_PLACEHOLDER = "0.0,0.0"


class CollectorWorkflowError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def find_shipment(shipment_id):
    return Shipment.query.get(shipment_id) or Shipment.query.filter_by(
        shipment_code=shipment_id
    ).first()


def resolve_gps(data=None, latitude=None, longitude=None):
    if latitude and longitude:
        return f"{latitude},{longitude}"

    if data:
        lat = data.get("latitude")
        lng = data.get("longitude")
        if lat and lng:
            return f"{lat},{lng}"

        gps = data.get("gps_location")
        if gps:
            return gps

    return GPS_PLACEHOLDER


def _get_transport_box(shipment):
    if not shipment.transport_box_id:
        return None

    return TransportBox.query.get(shipment.transport_box_id)


def _record_shipment_activity(
    shipment,
    *,
    audit_action,
    timeline_event,
    event_type,
    note,
    actor,
    gps_location,
    user_email,
):
    write_audit(
        action=audit_action,
        object_type="SHIPMENT",
        object_id=shipment.id,
        user_email=user_email or actor or "COLLECTOR",
    )

    timeline = ShipmentTimeline(
        shipment_id=shipment.id,
        event_type=timeline_event,
        note=note,
        actor=actor or user_email or "COLLECTOR",
        gps_location=gps_location,
        temperature=shipment.temperature,
    )
    db.session.add(timeline)

    write_event(
        event_type=event_type,
        object_type="SHIPMENT",
        object_id=shipment.id,
        message=note,
    )


def accept_shipment(shipment, *, collector_id=None, gps_location=None, actor=None):
    if shipment.status != SHIPMENT_CREATED:
        raise CollectorWorkflowError(
            f"Shipment must be {SHIPMENT_CREATED} to accept, got {shipment.status}"
        )

    shipment.status = SHIPMENT_ACCEPTED

    if collector_id:
        shipment.collector_id = collector_id

    shipment.gps_location = gps_location or GPS_PLACEHOLDER

    box = _get_transport_box(shipment)
    if box and box.status == BOX_ONLINE:
        box.status = BOX_IN_USE

    note = f"Collector accepted shipment {shipment.shipment_code}"
    _record_shipment_activity(
        shipment,
        audit_action="COLLECTOR_ACCEPT_SHIPMENT",
        timeline_event="COLLECTOR_ACCEPTED",
        event_type="COLLECTOR_ACCEPTED_SHIPMENT",
        note=note,
        actor=actor,
        gps_location=shipment.gps_location,
        user_email=actor,
    )

    db.session.commit()
    return shipment


def start_trip(shipment, *, collector_id=None, gps_location=None, actor=None):
    if shipment.status != SHIPMENT_ACCEPTED:
        raise CollectorWorkflowError(
            f"Shipment must be {SHIPMENT_ACCEPTED} to start trip, got {shipment.status}"
        )

    if collector_id and shipment.collector_id and shipment.collector_id != collector_id:
        raise CollectorWorkflowError(
            "Collector does not match assigned shipment",
            status_code=403,
        )

    if collector_id and not shipment.collector_id:
        shipment.collector_id = collector_id

    shipment.status = SHIPMENT_IN_TRANSIT
    shipment.departed_at = datetime.utcnow()
    shipment.gps_location = gps_location or shipment.gps_location or GPS_PLACEHOLDER

    box = _get_transport_box(shipment)
    if box:
        box.status = BOX_IN_TRANSIT

    note = f"Collector started trip for shipment {shipment.shipment_code}"
    _record_shipment_activity(
        shipment,
        audit_action="COLLECTOR_START_TRIP",
        timeline_event="TRIP_STARTED",
        event_type="SHIPMENT_TRIP_STARTED",
        note=note,
        actor=actor,
        gps_location=shipment.gps_location,
        user_email=actor,
    )

    db.session.commit()
    return shipment


def legacy_start_shipment(shipment, *, actor=None, gps_location=None, collector_id=None):
    if shipment.status == SHIPMENT_CREATED:
        accept_shipment(
            shipment,
            collector_id=collector_id or shipment.collector_id,
            gps_location=gps_location,
            actor=actor or "COLLECTOR",
        )

    if shipment.status == SHIPMENT_ACCEPTED:
        return start_trip(
            shipment,
            collector_id=collector_id or shipment.collector_id,
            gps_location=gps_location,
            actor=actor or "COLLECTOR",
        )

    if shipment.status == SHIPMENT_IN_TRANSIT:
        return shipment

    raise CollectorWorkflowError(
        f"Cannot start shipment from status {shipment.status}"
    )
