from datetime import datetime
import uuid

from app.core.audit import write_audit
from app.core.events import write_event
from app.core.statuses import (
    BOOKING_TIMELINE_COLLECTED,
    BOOKING_TIMELINE_IN_TRANSIT,
    BOOKING_TIMELINE_LAB_RECEIVED,
    COLLECTION_CHECKED_IN,
    COLLECTION_COLLECTED,
    COLLECTION_IN_TRANSIT,
    COLLECTION_PENDING,
    COLLECTION_RECEIVED,
    ORDER_COLLECTING,
    ORDER_IN_TRANSIT,
    ORDER_LAB_RECEIVED,
    ORDER_SAMPLE_COLLECTED,
    SAMPLE_EVENT_CHECKED_IN,
    SAMPLE_EVENT_COLLECTED,
    SAMPLE_EVENT_IN_TRANSIT,
    SAMPLE_EVENT_LAB_RECEIVED,
    SAMPLE_IN_TRANSIT,
    SAMPLE_RECEIVED,
)
from app.extensions.db import db
from app.models.driver import Driver
from app.models.sample_collection import SampleCollection
from app.models.sample_event import SampleEvent
from app.models.sample_tracking import SampleTracking
from app.services.booking_assignment import BookingAssignmentService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_lifecycle import OrderLifecycleError, OrderLifecycleService


class SampleCollectionWorkflowError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class SampleCollectionWorkflowService:

    @staticmethod
    def _get_booking_or_raise(booking_id):
        try:
            return OrderLifecycleService._get_booking_or_raise(booking_id)
        except OrderLifecycleError as exc:
            raise SampleCollectionWorkflowError(exc.message, exc.status_code)

    @staticmethod
    def _get_order_for_booking(booking_id):
        order = OrderLifecycleService.get_order_for_booking(booking_id)
        if not order:
            raise SampleCollectionWorkflowError(
                "Order must be created before sample collection",
                409,
            )
        return order

    @staticmethod
    def _get_or_create_collection(booking, order):
        collection = SampleCollection.query.filter_by(
            marketplace_booking_id=booking.id,
        ).first()
        if collection:
            return collection

        assignment = BookingAssignmentService.get_assignment_for_booking(booking.id)
        collector_name = None
        collector_id = None
        if assignment and assignment.collector_id:
            collector_id = assignment.collector_id
            collector = Driver.query.get(collector_id)
            collector_name = collector.full_name if collector else None

        collection = SampleCollection(
            order_id=order.id,
            marketplace_booking_id=booking.id,
            collector_id=collector_id,
            collector_name=collector_name,
            status=COLLECTION_PENDING,
        )
        db.session.add(collection)
        db.session.flush()
        return collection

    @staticmethod
    def _sample_code():
        return "SMP-" + datetime.utcnow().strftime("%Y%m%d") + "-" + str(uuid.uuid4())[:8].upper()

    @staticmethod
    def _write_sample_event(sample_tracking_id, event_type, note=None):
        event = SampleEvent(
            sample_tracking_id=sample_tracking_id,
            event_type=event_type,
            note=note,
        )
        db.session.add(event)
        return event

    @staticmethod
    def get_collection_for_booking(booking_id):
        SampleCollectionWorkflowService._get_booking_or_raise(booking_id)
        collection = SampleCollection.query.filter_by(
            marketplace_booking_id=booking_id,
        ).first()
        if not collection:
            return None

        payload = collection.to_dict()
        if collection.sample_tracking_id:
            sample = SampleTracking.query.get(collection.sample_tracking_id)
            payload["sample_tracking"] = sample.to_dict() if sample else None
        else:
            payload["sample_tracking"] = None
        return payload

    @staticmethod
    def check_in_collection(
        booking_id,
        actor_email="SYSTEM",
        ip_address="",
    ):
        booking = SampleCollectionWorkflowService._get_booking_or_raise(booking_id)
        order = SampleCollectionWorkflowService._get_order_for_booking(booking_id)
        collection = SampleCollectionWorkflowService._get_or_create_collection(booking, order)

        if collection.status not in (COLLECTION_PENDING,):
            raise SampleCollectionWorkflowError(
                f"Collection cannot be checked in from status {collection.status}",
                409,
            )

        collection.status = COLLECTION_CHECKED_IN
        order.status = ORDER_COLLECTING
        order.updated_at = datetime.utcnow() if hasattr(order, "updated_at") else None
        booking.updated_at = datetime.utcnow()

        write_audit(
            action="SAMPLE_COLLECTION_CHECKED_IN",
            object_type="SampleCollection",
            object_id=collection.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        write_event(
            event_type="SAMPLE_COLLECTION_CHECKED_IN",
            object_type="SampleCollection",
            object_id=collection.id,
            message=f"Collector checked in for booking {booking.booking_code}",
        )

        db.session.commit()
        return collection

    @staticmethod
    def record_collection(
        booking_id,
        collector_id=None,
        note=None,
        latitude=None,
        longitude=None,
        actor_email="SYSTEM",
        ip_address="",
    ):
        booking = SampleCollectionWorkflowService._get_booking_or_raise(booking_id)
        order = SampleCollectionWorkflowService._get_order_for_booking(booking_id)
        collection = SampleCollectionWorkflowService._get_or_create_collection(booking, order)

        if collection.status not in (COLLECTION_PENDING, COLLECTION_CHECKED_IN):
            raise SampleCollectionWorkflowError(
                f"Sample cannot be collected from status {collection.status}",
                409,
            )

        assignment = BookingAssignmentService.get_assignment_for_booking(booking.id)
        resolved_collector_id = collector_id or (assignment.collector_id if assignment else None)
        collector_name = collection.collector_name
        if resolved_collector_id:
            collector = Driver.query.get(resolved_collector_id)
            if collector:
                collector_name = collector.full_name
            collection.collector_id = resolved_collector_id

        sample = SampleTracking.query.filter_by(marketplace_booking_id=booking.id).first()
        if not sample:
            sample = SampleTracking(
                sample_code=SampleCollectionWorkflowService._sample_code(),
                marketplace_booking_id=booking.id,
                collector_id=resolved_collector_id,
                latitude=latitude,
                longitude=longitude,
                status=SAMPLE_IN_TRANSIT,
            )
            db.session.add(sample)
            db.session.flush()
        else:
            sample.collector_id = resolved_collector_id or sample.collector_id
            sample.latitude = latitude or sample.latitude
            sample.longitude = longitude or sample.longitude
            sample.status = SAMPLE_IN_TRANSIT
            sample.updated_at = datetime.utcnow()

        collection.sample_tracking_id = sample.id
        collection.collector_name = collector_name
        collection.status = COLLECTION_COLLECTED
        collection.collected_at = datetime.utcnow()
        order.status = ORDER_SAMPLE_COLLECTED
        booking.updated_at = datetime.utcnow()

        SampleCollectionWorkflowService._write_sample_event(
            sample.id,
            SAMPLE_EVENT_COLLECTED,
            note=note or f"Sample collected for booking {booking.booking_code}",
        )

        MarketplaceBookingService.write_timeline_event(
            booking,
            BOOKING_TIMELINE_COLLECTED,
            message=note or f"Sample collected for booking {booking.booking_code}",
            actor_email=actor_email,
            audit_action="SAMPLE_COLLECTED",
            ip_address=ip_address,
        )

        db.session.commit()
        return collection, sample

    @staticmethod
    def dispatch_sample(
        booking_id,
        transport_box_id=None,
        note=None,
        actor_email="SYSTEM",
        ip_address="",
    ):
        booking = SampleCollectionWorkflowService._get_booking_or_raise(booking_id)
        order = SampleCollectionWorkflowService._get_order_for_booking(booking_id)
        collection = SampleCollection.query.filter_by(
            marketplace_booking_id=booking.id,
        ).first()
        if not collection or collection.status != COLLECTION_COLLECTED:
            raise SampleCollectionWorkflowError(
                "Sample must be collected before dispatch",
                409,
            )

        sample = SampleTracking.query.get(collection.sample_tracking_id)
        if not sample:
            raise SampleCollectionWorkflowError("Sample tracking record not found", 404)

        if transport_box_id:
            sample.transport_box_id = transport_box_id
        sample.status = SAMPLE_IN_TRANSIT
        sample.updated_at = datetime.utcnow()
        collection.status = COLLECTION_IN_TRANSIT
        order.status = ORDER_IN_TRANSIT
        booking.updated_at = datetime.utcnow()

        SampleCollectionWorkflowService._write_sample_event(
            sample.id,
            SAMPLE_EVENT_IN_TRANSIT,
            note=note or f"Sample dispatched for booking {booking.booking_code}",
        )

        MarketplaceBookingService.write_timeline_event(
            booking,
            BOOKING_TIMELINE_IN_TRANSIT,
            message=note or f"Sample in transit for booking {booking.booking_code}",
            actor_email=actor_email,
            audit_action="SAMPLE_IN_TRANSIT",
            ip_address=ip_address,
        )

        db.session.commit()
        return collection, sample

    @staticmethod
    def receive_at_lab(
        booking_id,
        note=None,
        actor_email="SYSTEM",
        ip_address="",
    ):
        booking = SampleCollectionWorkflowService._get_booking_or_raise(booking_id)
        order = SampleCollectionWorkflowService._get_order_for_booking(booking_id)
        collection = SampleCollection.query.filter_by(
            marketplace_booking_id=booking.id,
        ).first()
        if not collection or collection.status not in (
            COLLECTION_COLLECTED,
            COLLECTION_IN_TRANSIT,
        ):
            raise SampleCollectionWorkflowError(
                "Sample must be collected or in transit before lab receive",
                409,
            )

        sample = SampleTracking.query.get(collection.sample_tracking_id)
        if not sample:
            raise SampleCollectionWorkflowError("Sample tracking record not found", 404)

        sample.status = SAMPLE_RECEIVED
        sample.updated_at = datetime.utcnow()
        collection.status = COLLECTION_RECEIVED
        order.status = ORDER_LAB_RECEIVED
        booking.updated_at = datetime.utcnow()

        SampleCollectionWorkflowService._write_sample_event(
            sample.id,
            SAMPLE_EVENT_LAB_RECEIVED,
            note=note or f"Sample received at lab for booking {booking.booking_code}",
        )

        MarketplaceBookingService.write_timeline_event(
            booking,
            BOOKING_TIMELINE_LAB_RECEIVED,
            message=note or f"Sample received at lab for booking {booking.booking_code}",
            actor_email=actor_email,
            audit_action="SAMPLE_LAB_RECEIVED",
            ip_address=ip_address,
        )

        db.session.commit()
        return collection, sample
