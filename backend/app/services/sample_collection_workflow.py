from datetime import datetime, timedelta
import logging
import uuid
from typing import Optional, Set

from sqlalchemy import or_
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import load_only

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
    COLLECTION_QUEUE_STATUSES,
    COLLECTION_RECEIVED,
    COLLECTION_RECOLLECT_REQUIRED,
    COLLECTION_REJECTED,
    ORDER_COLLECTING,
    ORDER_IN_TRANSIT,
    ORDER_LAB_RECEIVED,
    ORDER_SAMPLE_COLLECTED,
    SAMPLE_EVENT_CHECKED_IN,
    SAMPLE_EVENT_COLLECTED,
    SAMPLE_EVENT_DISPATCH,
    SAMPLE_EVENT_HANDOFF,
    SAMPLE_EVENT_IN_TRANSIT,
    SAMPLE_EVENT_LAB_RECEIVED,
    SAMPLE_EVENT_PICKUP,
    SAMPLE_EVENT_RECOLLECT,
    SAMPLE_EVENT_REJECTED,
    SAMPLE_IN_TRANSIT,
    SAMPLE_QUALITY_ACCEPTABLE,
    SAMPLE_QUALITY_MISMATCHED_ID,
    SAMPLE_QUALITY_REJECTION_STATUSES,
    SAMPLE_RECEIVED,
    VALID_SAMPLE_QUALITY_STATUSES,
)
from app.extensions.db import db
from app.models.audit_log import AuditLog
from app.models.driver import Driver
from app.models.marketplace_booking import MarketplaceBooking
from app.models.sample_collection import SampleCollection
from app.models.sample_event import SampleEvent
from app.models.sample_tracking import SampleTracking
from app.services.booking_assignment import BookingAssignmentService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_lifecycle import OrderLifecycleError, OrderLifecycleService

logger = logging.getLogger("dxcon.sample_collection")


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
    def _get_collection_or_raise(collection_id):
        collection = SampleCollection.query.get(collection_id)
        if not collection:
            raise SampleCollectionWorkflowError("Sample collection not found", 404)
        return collection

    @staticmethod
    def _expected_barcode_for(booking, order, collection=None):
        if collection and collection.expected_barcode:
            return collection.expected_barcode
        if collection and collection.barcode_value:
            return collection.barcode_value
        sample = SampleTracking.query.filter_by(marketplace_booking_id=booking.id).first()
        if sample and sample.sample_code:
            return sample.sample_code
        order_barcode = getattr(order, "barcode_value", None)
        if order_barcode:
            return order_barcode
        return f"BC-{booking.booking_code}"

    @staticmethod
    def _normalize_barcode(value):
        if value is None:
            return None
        return str(value).strip().upper()

    @staticmethod
    def _get_or_create_collection(booking, order):
        collection = SampleCollection.query.filter_by(
            marketplace_booking_id=booking.id,
        ).filter(
            SampleCollection.status != COLLECTION_REJECTED,
        ).order_by(SampleCollection.created_at.desc()).first()

        # Prefer open queue statuses; fall back to any non-rejected row
        if collection and collection.status in (
            COLLECTION_COLLECTED,
            COLLECTION_IN_TRANSIT,
            COLLECTION_RECEIVED,
        ):
            return collection

        open_collection = SampleCollection.query.filter_by(
            marketplace_booking_id=booking.id,
        ).filter(
            SampleCollection.status.in_(COLLECTION_QUEUE_STATUSES),
        ).order_by(SampleCollection.created_at.desc()).first()
        if open_collection:
            return open_collection

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
            partner_id=booking.partner_id,
            location_city=booking.city,
            collection_location=booking.patient_address,
            expected_barcode=f"BC-{booking.booking_code}",
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
    def _sample_collection_db_columns() -> Set[str]:
        """Live DB columns for sample_collections (empty set if table missing)."""
        try:
            from app.infrastructure.schema_introspection import get_table_columns

            return get_table_columns("sample_collections")
        except Exception:
            return set()

    @staticmethod
    def _load_only_existing_columns(columns: Set[str]):
        """Restrict SELECT to physical columns so missing ORM fields do not 500."""
        attrs = [
            getattr(SampleCollection, column.name)
            for column in SampleCollection.__table__.columns
            if column.name in columns
        ]
        if not attrs:
            return None
        return load_only(*attrs)

    @staticmethod
    def _collection_to_dict_compatible(collection, columns: Optional[Set[str]] = None) -> dict:
        """Serialize without touching columns absent from the live schema."""
        columns = columns if columns is not None else SampleCollectionWorkflowService._sample_collection_db_columns()
        if not columns:
            # Fall back to model to_dict when introspection unavailable (e.g. tests with create_all).
            return collection.to_dict()

        def _get(name, default=None):
            if name not in columns:
                return default
            return getattr(collection, name, default)

        def _iso(value):
            return value.isoformat() if value else None

        return {
            "id": _get("id"),
            "order_id": _get("order_id"),
            "marketplace_booking_id": _get("marketplace_booking_id"),
            "collector_id": _get("collector_id"),
            "sample_tracking_id": _get("sample_tracking_id"),
            "collector_name": _get("collector_name"),
            "status": _get("status"),
            "collected_at": _iso(_get("collected_at")),
            "created_at": _iso(_get("created_at")),
            "specimen_type": _get("specimen_type"),
            "barcode_value": _get("barcode_value"),
            "expected_barcode": _get("expected_barcode"),
            "collection_location": _get("collection_location"),
            "location_city": _get("location_city"),
            "notes": _get("notes"),
            "quality_status": _get("quality_status"),
            "rejection_reason": _get("rejection_reason"),
            "partner_id": _get("partner_id"),
            "recollect_of_id": _get("recollect_of_id"),
            "patient_verified": bool(_get("patient_verified") or False),
            "order_verified": bool(_get("order_verified") or False),
            "picked_up_at": _iso(_get("picked_up_at")),
            "dispatched_at": _iso(_get("dispatched_at")),
            "handoff_at": _iso(_get("handoff_at")),
            "arrived_at_lab": _iso(_get("arrived_at_lab")),
            "vehicle_id": _get("vehicle_id"),
            "driver_id": _get("driver_id"),
            "transport_box_id": _get("transport_box_id"),
            "distance_km": _get("distance_km"),
            "eta_minutes": _get("eta_minutes"),
            "temperature_c": _get("temperature_c"),
            "iot_device_id": _get("iot_device_id"),
            "updated_at": _iso(_get("updated_at")),
        }

    @staticmethod
    def _enrich_payload(collection, columns: Optional[Set[str]] = None):
        columns = columns if columns is not None else SampleCollectionWorkflowService._sample_collection_db_columns()
        # Empty columns → full schema assumed (unit tests / create_all)
        if columns and (
            "marketplace_booking_id" not in columns
            or len(columns) < len(SampleCollection.__table__.columns)
        ):
            payload = SampleCollectionWorkflowService._collection_to_dict_compatible(collection, columns)
        else:
            payload = collection.to_dict()

        tracking_id = payload.get("sample_tracking_id")
        if tracking_id:
            try:
                sample = SampleTracking.query.get(tracking_id)
                payload["sample_tracking"] = sample.to_dict() if sample else None
            except (OperationalError, ProgrammingError):
                db.session.rollback()
                payload["sample_tracking"] = None
        else:
            payload["sample_tracking"] = None

        booking = None
        booking_id = payload.get("marketplace_booking_id")
        if booking_id:
            try:
                booking = MarketplaceBooking.query.get(booking_id)
            except (OperationalError, ProgrammingError):
                db.session.rollback()
                booking = None
        if booking:
            payload["booking"] = {
                "id": booking.id,
                "booking_code": booking.booking_code,
                "patient_name": booking.patient_name,
                "patient_phone": booking.patient_phone,
                "patient_address": booking.patient_address,
                "city": booking.city,
                "partner_id": booking.partner_id,
            }
            try:
                order = OrderLifecycleService.get_order_for_booking(booking.id)
                payload["order"] = order.to_dict() if order else None
            except Exception:
                payload["order"] = None
            payload["source"] = "field"
        else:
            # Desk / Reception SampleCollection (order_id → BizOrder)
            payload["source"] = "desk"
            biz_order = None
            order_id = payload.get("order_id")
            if order_id:
                try:
                    from app.models.biz_order import BizOrder

                    biz_order = BizOrder.query.get(order_id)
                except (OperationalError, ProgrammingError):
                    db.session.rollback()
                    biz_order = None
            if biz_order:
                payload["order"] = biz_order.to_dict()
                payload["booking"] = {
                    "id": biz_order.id,
                    "booking_code": biz_order.order_code,
                    "patient_name": biz_order.patient_name,
                    "patient_phone": None,
                    "patient_address": payload.get("collection_location") or "Reception Desk",
                    "city": payload.get("location_city"),
                    "partner_id": None,
                }
            else:
                payload["booking"] = None
                payload["order"] = None
        return payload

    @staticmethod
    def list_queue(
        *,
        status=None,
        collector_id=None,
        location=None,
        date_from=None,
        date_to=None,
        partner_id=None,
        awaiting_only=True,
    ):
        columns = SampleCollectionWorkflowService._sample_collection_db_columns()
        query = SampleCollection.query
        load_opt = None
        if columns:
            load_opt = SampleCollectionWorkflowService._load_only_existing_columns(columns)
            if load_opt is not None:
                query = query.options(load_opt)
            elif "id" not in columns:
                logger.warning("sample_collections has no selectable columns; returning empty queue")
                return []

        if awaiting_only and not status:
            query = query.filter(SampleCollection.status.in_(COLLECTION_QUEUE_STATUSES))
        elif status:
            from app.sample_collection_workspace.desk_bridge import resolve_filter_statuses

            statuses = resolve_filter_statuses(status) or [
                s.strip() for s in str(status).split(",") if s.strip()
            ]
            if len(statuses) == 1:
                query = query.filter(SampleCollection.status == statuses[0])
            else:
                query = query.filter(SampleCollection.status.in_(statuses))

        # Optional filters — skip when column absent on legacy production schema
        if collector_id and (not columns or "collector_id" in columns):
            query = query.filter(SampleCollection.collector_id == collector_id)
        if partner_id and (not columns or "partner_id" in columns):
            query = query.filter(SampleCollection.partner_id == partner_id)
        if location:
            like = f"%{location}%"
            loc_clauses = []
            if not columns or "location_city" in columns:
                loc_clauses.append(SampleCollection.location_city.ilike(like))
            if not columns or "collection_location" in columns:
                loc_clauses.append(SampleCollection.collection_location.ilike(like))
            if loc_clauses:
                query = query.filter(or_(*loc_clauses))

        if date_from and (not columns or "created_at" in columns):
            try:
                start = datetime.fromisoformat(str(date_from).replace("Z", ""))
                query = query.filter(SampleCollection.created_at >= start)
            except ValueError:
                raise SampleCollectionWorkflowError("Invalid date_from (ISO8601 expected)")
        if date_to and (not columns or "created_at" in columns):
            try:
                end = datetime.fromisoformat(str(date_to).replace("Z", ""))
                if len(str(date_to)) <= 10:
                    end = end + timedelta(days=1)
                query = query.filter(SampleCollection.created_at < end)
            except ValueError:
                raise SampleCollectionWorkflowError("Invalid date_to (ISO8601 expected)")

        try:
            collections = query.order_by(SampleCollection.created_at.desc()).all()
        except (OperationalError, ProgrammingError) as exc:
            db.session.rollback()
            logger.exception(
                "sample collection queue query failed; apply "
                "backend/migrations/020_sample_collections_marketplace_booking_id.sql"
            )
            # Backward compatible: empty queue rather than HTTP 500 for schema drift
            raise SampleCollectionWorkflowError(
                "Sample collection schema is out of date; apply "
                "backend/migrations/020_sample_collections_marketplace_booking_id.sql",
                503,
            ) from exc

        return [
            SampleCollectionWorkflowService._enrich_payload(item, columns)
            for item in collections
        ]

    @staticmethod
    def get_collection(collection_id):
        collection = SampleCollectionWorkflowService._get_collection_or_raise(collection_id)
        return SampleCollectionWorkflowService._enrich_payload(collection)

    @staticmethod
    def get_collection_for_booking(booking_id):
        SampleCollectionWorkflowService._get_booking_or_raise(booking_id)
        collection = SampleCollection.query.filter_by(
            marketplace_booking_id=booking_id,
        ).order_by(SampleCollection.created_at.desc()).first()
        if not collection:
            return None
        return SampleCollectionWorkflowService._enrich_payload(collection)

    @staticmethod
    def ensure_collection_for_booking(booking_id, actor_email="SYSTEM", ip_address=""):
        booking = SampleCollectionWorkflowService._get_booking_or_raise(booking_id)
        order = SampleCollectionWorkflowService._get_order_for_booking(booking_id)
        collection = SampleCollectionWorkflowService._get_or_create_collection(booking, order)
        collection.expected_barcode = SampleCollectionWorkflowService._expected_barcode_for(
            booking, order, collection
        )
        collection.partner_id = collection.partner_id or booking.partner_id
        collection.location_city = collection.location_city or booking.city
        write_audit(
            action="SAMPLE_COLLECTION_ENSURED",
            object_type="SampleCollection",
            object_id=collection.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        db.session.commit()
        return collection

    @staticmethod
    def check_in_collection(
        booking_id,
        actor_email="SYSTEM",
        ip_address="",
    ):
        booking = SampleCollectionWorkflowService._get_booking_or_raise(booking_id)
        order = SampleCollectionWorkflowService._get_order_for_booking(booking_id)
        collection = SampleCollectionWorkflowService._get_or_create_collection(booking, order)

        if collection.status not in (COLLECTION_PENDING, COLLECTION_RECOLLECT_REQUIRED):
            raise SampleCollectionWorkflowError(
                f"Collection cannot be checked in from status {collection.status}",
                409,
            )

        collection.status = COLLECTION_CHECKED_IN
        collection.updated_at = datetime.utcnow()
        order.status = ORDER_COLLECTING
        if hasattr(order, "updated_at"):
            order.updated_at = datetime.utcnow()
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
    def verify_identifiers(
        collection_id,
        *,
        patient_name=None,
        booking_code=None,
        order_id=None,
        scanned_barcode=None,
        actor_email="SYSTEM",
        ip_address="",
    ):
        collection = SampleCollectionWorkflowService._get_collection_or_raise(collection_id)

        # Desk / Reception path — no marketplace booking
        if not collection.marketplace_booking_id:
            from app.models.biz_order import BizOrder

            biz_order = BizOrder.query.get(collection.order_id)
            if not biz_order:
                raise SampleCollectionWorkflowError("Desk order not found for collection", 404)

            mismatches = []
            if patient_name and patient_name.strip().lower() != (biz_order.patient_name or "").strip().lower():
                mismatches.append("patient_name")
            if booking_code and booking_code.strip().upper() != biz_order.order_code.upper():
                mismatches.append("booking_code")
            if order_id and order_id not in (biz_order.id, biz_order.order_code):
                mismatches.append("order_id")

            expected = (
                collection.expected_barcode
                or biz_order.barcode_value
                or f"BC-{biz_order.order_code}"
            )
            collection.expected_barcode = expected
            if scanned_barcode:
                scanned = SampleCollectionWorkflowService._normalize_barcode(scanned_barcode)
                accepted = {
                    SampleCollectionWorkflowService._normalize_barcode(expected),
                    SampleCollectionWorkflowService._normalize_barcode(biz_order.order_code),
                    SampleCollectionWorkflowService._normalize_barcode(f"BC-{biz_order.order_code}"),
                    SampleCollectionWorkflowService._normalize_barcode(biz_order.barcode_value),
                }
                if scanned not in accepted:
                    mismatches.append("barcode")

            if mismatches:
                write_audit(
                    action="SAMPLE_COLLECTION_VERIFY_FAILED",
                    object_type="SampleCollection",
                    object_id=collection.id,
                    user_email=actor_email,
                    ip_address=ip_address,
                )
                raise SampleCollectionWorkflowError(
                    f"Identifier mismatch: {', '.join(mismatches)}",
                    409,
                )

            collection.patient_verified = True
            collection.order_verified = True
            if collection.status == COLLECTION_PENDING:
                collection.status = COLLECTION_CHECKED_IN
            collection.updated_at = datetime.utcnow()
            write_audit(
                action="SAMPLE_COLLECTION_VERIFIED",
                object_type="SampleCollection",
                object_id=collection.id,
                user_email=actor_email,
                ip_address=ip_address,
            )
            db.session.commit()
            return collection

        booking = SampleCollectionWorkflowService._get_booking_or_raise(
            collection.marketplace_booking_id
        )
        order = SampleCollectionWorkflowService._get_order_for_booking(booking.id)

        mismatches = []
        if patient_name and patient_name.strip().lower() != (booking.patient_name or "").strip().lower():
            mismatches.append("patient_name")
        if booking_code and booking_code.strip().upper() != booking.booking_code.upper():
            mismatches.append("booking_code")
        if order_id and order_id not in (order.id, getattr(order, "order_code", None)):
            mismatches.append("order_id")

        expected = SampleCollectionWorkflowService._expected_barcode_for(booking, order, collection)
        collection.expected_barcode = expected
        if scanned_barcode:
            scanned = SampleCollectionWorkflowService._normalize_barcode(scanned_barcode)
            expected_norm = SampleCollectionWorkflowService._normalize_barcode(expected)
            alt = SampleCollectionWorkflowService._normalize_barcode(booking.booking_code)
            if scanned not in {expected_norm, alt, SampleCollectionWorkflowService._normalize_barcode(f"BC-{booking.booking_code}")}:
                mismatches.append("barcode")

        if mismatches:
            write_audit(
                action="SAMPLE_COLLECTION_VERIFY_FAILED",
                object_type="SampleCollection",
                object_id=collection.id,
                user_email=actor_email,
                ip_address=ip_address,
            )
            raise SampleCollectionWorkflowError(
                f"Identifier mismatch: {', '.join(mismatches)}",
                409,
            )

        collection.patient_verified = True
        collection.order_verified = True
        collection.updated_at = datetime.utcnow()
        write_audit(
            action="SAMPLE_COLLECTION_VERIFIED",
            object_type="SampleCollection",
            object_id=collection.id,
            user_email=actor_email,
            ip_address=ip_address,
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
        *,
        specimen_type=None,
        scanned_barcode=None,
        collection_location=None,
        require_barcode=False,
        patient_verified=None,
        order_verified=None,
        allow_notes=True,
    ):
        booking = SampleCollectionWorkflowService._get_booking_or_raise(booking_id)
        order = SampleCollectionWorkflowService._get_order_for_booking(booking_id)
        collection = SampleCollectionWorkflowService._get_or_create_collection(booking, order)

        if collection.status not in (
            COLLECTION_PENDING,
            COLLECTION_CHECKED_IN,
            COLLECTION_RECOLLECT_REQUIRED,
        ):
            raise SampleCollectionWorkflowError(
                f"Sample cannot be collected from status {collection.status}",
                409,
            )

        # Duplicate guard: another active collected specimen for same booking
        duplicate = SampleCollection.query.filter_by(
            marketplace_booking_id=booking.id,
            status=COLLECTION_COLLECTED,
        ).filter(SampleCollection.id != collection.id).first()
        if duplicate:
            raise SampleCollectionWorkflowError(
                "Duplicate collection prevented: specimen already collected for this order",
                409,
            )

        expected = SampleCollectionWorkflowService._expected_barcode_for(booking, order, collection)
        collection.expected_barcode = expected

        if require_barcode and not scanned_barcode:
            raise SampleCollectionWorkflowError("scanned_barcode is required", 400)

        if scanned_barcode:
            scanned = SampleCollectionWorkflowService._normalize_barcode(scanned_barcode)
            expected_norm = SampleCollectionWorkflowService._normalize_barcode(expected)
            accepted = {
                expected_norm,
                SampleCollectionWorkflowService._normalize_barcode(booking.booking_code),
                SampleCollectionWorkflowService._normalize_barcode(f"BC-{booking.booking_code}"),
            }
            if scanned not in accepted:
                collection.quality_status = SAMPLE_QUALITY_MISMATCHED_ID
                write_audit(
                    action="SAMPLE_COLLECTION_BARCODE_MISMATCH",
                    object_type="SampleCollection",
                    object_id=collection.id,
                    user_email=actor_email,
                    ip_address=ip_address,
                )
                db.session.commit()
                raise SampleCollectionWorkflowError(
                    "Barcode mismatch: scanned identifier does not match expected specimen/order barcode",
                    409,
                )
            collection.barcode_value = scanned_barcode.strip()

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

        now = datetime.utcnow()
        collection.sample_tracking_id = sample.id
        collection.collector_name = collector_name
        collection.status = COLLECTION_COLLECTED
        collection.collected_at = now
        collection.picked_up_at = collection.picked_up_at or now
        collection.specimen_type = specimen_type or collection.specimen_type or "BLOOD"
        collection.collection_location = (
            collection_location
            or collection.collection_location
            or booking.patient_address
        )
        collection.location_city = collection.location_city or booking.city
        collection.partner_id = collection.partner_id or booking.partner_id
        collection.quality_status = SAMPLE_QUALITY_ACCEPTABLE
        collection.updated_at = now
        if patient_verified is not None:
            collection.patient_verified = bool(patient_verified)
        if order_verified is not None:
            collection.order_verified = bool(order_verified)
        if allow_notes and note:
            collection.notes = note

        order.status = ORDER_SAMPLE_COLLECTED
        booking.updated_at = now

        SampleCollectionWorkflowService._write_sample_event(
            sample.id,
            SAMPLE_EVENT_COLLECTED,
            note=note or f"Sample collected for booking {booking.booking_code}",
        )
        SampleCollectionWorkflowService._write_sample_event(
            sample.id,
            SAMPLE_EVENT_PICKUP,
            note=f"Pickup recorded at {now.isoformat()}",
        )

        MarketplaceBookingService.write_timeline_event(
            booking,
            BOOKING_TIMELINE_COLLECTED,
            message=note or f"Sample collected for booking {booking.booking_code}",
            actor_email=actor_email,
            audit_action="SAMPLE_COLLECTED",
            ip_address=ip_address,
        )

        write_audit(
            action="SAMPLE_COLLECTION_COLLECTED",
            object_type="SampleCollection",
            object_id=collection.id,
            user_email=actor_email,
            ip_address=ip_address,
        )

        db.session.commit()
        return collection, sample

    @staticmethod
    def reject_specimen(
        collection_id,
        *,
        quality_status,
        rejection_reason=None,
        actor_email="SYSTEM",
        ip_address="",
        request_recollect=True,
    ):
        collection = SampleCollectionWorkflowService._get_collection_or_raise(collection_id)
        if quality_status not in VALID_SAMPLE_QUALITY_STATUSES:
            raise SampleCollectionWorkflowError(
                f"Invalid quality_status. Must be one of: {', '.join(VALID_SAMPLE_QUALITY_STATUSES)}"
            )
        if quality_status not in SAMPLE_QUALITY_REJECTION_STATUSES:
            raise SampleCollectionWorkflowError(
                "quality_status must be a rejection status for reject_specimen"
            )

        if collection.status in (COLLECTION_RECEIVED,):
            raise SampleCollectionWorkflowError(
                f"Cannot reject specimen in status {collection.status}",
                409,
            )

        collection.status = COLLECTION_REJECTED
        collection.quality_status = quality_status
        collection.rejection_reason = rejection_reason or quality_status
        collection.updated_at = datetime.utcnow()

        if collection.sample_tracking_id:
            SampleCollectionWorkflowService._write_sample_event(
                collection.sample_tracking_id,
                SAMPLE_EVENT_REJECTED,
                note=collection.rejection_reason,
            )

        write_audit(
            action="SAMPLE_COLLECTION_REJECTED",
            object_type="SampleCollection",
            object_id=collection.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        write_event(
            event_type="SAMPLE_COLLECTION_REJECTED",
            object_type="SampleCollection",
            object_id=collection.id,
            message=collection.rejection_reason,
        )

        recollect = None
        if request_recollect and collection.marketplace_booking_id:
            recollect = SampleCollectionWorkflowService.request_recollect(
                collection.id,
                actor_email=actor_email,
                ip_address=ip_address,
                commit=False,
            )

        db.session.commit()
        return collection, recollect

    @staticmethod
    def request_recollect(
        collection_id,
        *,
        actor_email="SYSTEM",
        ip_address="",
        commit=True,
        specimen_type=None,
    ):
        original = SampleCollectionWorkflowService._get_collection_or_raise(collection_id)
        if not original.marketplace_booking_id:
            raise SampleCollectionWorkflowError("Recollection requires a marketplace booking", 409)

        booking = SampleCollectionWorkflowService._get_booking_or_raise(
            original.marketplace_booking_id
        )
        order = SampleCollectionWorkflowService._get_order_for_booking(booking.id)

        existing_open = SampleCollection.query.filter_by(
            marketplace_booking_id=booking.id,
        ).filter(
            SampleCollection.status.in_(COLLECTION_QUEUE_STATUSES),
        ).filter(SampleCollection.id != original.id).first()
        if existing_open:
            if commit:
                db.session.commit()
            return existing_open

        if original.status not in (
            COLLECTION_REJECTED,
            COLLECTION_COLLECTED,
            COLLECTION_RECOLLECT_REQUIRED,
        ):
            original.status = COLLECTION_RECOLLECT_REQUIRED

        recollect = SampleCollection(
            order_id=order.id,
            marketplace_booking_id=booking.id,
            collector_id=original.collector_id,
            collector_name=original.collector_name,
            status=COLLECTION_RECOLLECT_REQUIRED,
            partner_id=original.partner_id or booking.partner_id,
            location_city=original.location_city or booking.city,
            collection_location=original.collection_location or booking.patient_address,
            expected_barcode=SampleCollectionWorkflowService._expected_barcode_for(
                booking, order, original
            ),
            specimen_type=specimen_type or original.specimen_type,
            recollect_of_id=original.id,
        )
        db.session.add(recollect)
        db.session.flush()

        if original.sample_tracking_id:
            SampleCollectionWorkflowService._write_sample_event(
                original.sample_tracking_id,
                SAMPLE_EVENT_RECOLLECT,
                note=f"Recollect requested → {recollect.id}",
            )

        write_audit(
            action="SAMPLE_COLLECTION_RECOLLECT_REQUESTED",
            object_type="SampleCollection",
            object_id=recollect.id,
            user_email=actor_email,
            ip_address=ip_address,
        )

        if commit:
            db.session.commit()
        return recollect

    @staticmethod
    def dispatch_sample(
        booking_id,
        transport_box_id=None,
        note=None,
        actor_email="SYSTEM",
        ip_address="",
        *,
        vehicle_id=None,
        driver_id=None,
        distance_km=None,
        eta_minutes=None,
        temperature_c=None,
        iot_device_id=None,
    ):
        booking = SampleCollectionWorkflowService._get_booking_or_raise(booking_id)
        order = SampleCollectionWorkflowService._get_order_for_booking(booking_id)
        collection = SampleCollection.query.filter_by(
            marketplace_booking_id=booking.id,
        ).filter(
            SampleCollection.status == COLLECTION_COLLECTED,
        ).order_by(SampleCollection.created_at.desc()).first()
        if not collection:
            raise SampleCollectionWorkflowError(
                "Sample must be collected before dispatch",
                409,
            )

        sample = SampleTracking.query.get(collection.sample_tracking_id)
        if not sample:
            raise SampleCollectionWorkflowError("Sample tracking record not found", 404)

        now = datetime.utcnow()
        if transport_box_id:
            sample.transport_box_id = transport_box_id
            collection.transport_box_id = transport_box_id
        sample.status = SAMPLE_IN_TRANSIT
        sample.updated_at = now
        collection.status = COLLECTION_IN_TRANSIT
        collection.dispatched_at = now
        collection.updated_at = now
        if vehicle_id:
            collection.vehicle_id = vehicle_id
        if driver_id:
            collection.driver_id = driver_id
        if distance_km is not None:
            collection.distance_km = float(distance_km)
        if eta_minutes is not None:
            collection.eta_minutes = int(eta_minutes)
        if temperature_c is not None:
            collection.temperature_c = float(temperature_c)
        if iot_device_id:
            collection.iot_device_id = iot_device_id

        order.status = ORDER_IN_TRANSIT
        booking.updated_at = now

        SampleCollectionWorkflowService._write_sample_event(
            sample.id,
            SAMPLE_EVENT_IN_TRANSIT,
            note=note or f"Sample dispatched for booking {booking.booking_code}",
        )
        SampleCollectionWorkflowService._write_sample_event(
            sample.id,
            SAMPLE_EVENT_DISPATCH,
            note=note or f"Dispatch at {now.isoformat()}",
        )

        MarketplaceBookingService.write_timeline_event(
            booking,
            BOOKING_TIMELINE_IN_TRANSIT,
            message=note or f"Sample in transit for booking {booking.booking_code}",
            actor_email=actor_email,
            audit_action="SAMPLE_IN_TRANSIT",
            ip_address=ip_address,
        )

        write_audit(
            action="SAMPLE_COLLECTION_DISPATCHED",
            object_type="SampleCollection",
            object_id=collection.id,
            user_email=actor_email,
            ip_address=ip_address,
        )

        db.session.commit()
        return collection, sample

    @staticmethod
    def record_handoff(
        collection_id,
        *,
        note=None,
        temperature_c=None,
        actor_email="SYSTEM",
        ip_address="",
    ):
        collection = SampleCollectionWorkflowService._get_collection_or_raise(collection_id)
        if collection.status not in (COLLECTION_COLLECTED, COLLECTION_IN_TRANSIT):
            raise SampleCollectionWorkflowError(
                f"Cannot hand off sample in status {collection.status}",
                409,
            )
        now = datetime.utcnow()
        collection.handoff_at = now
        collection.updated_at = now
        if temperature_c is not None:
            collection.temperature_c = float(temperature_c)
        if collection.status == COLLECTION_COLLECTED:
            collection.status = COLLECTION_IN_TRANSIT

        if collection.sample_tracking_id:
            SampleCollectionWorkflowService._write_sample_event(
                collection.sample_tracking_id,
                SAMPLE_EVENT_HANDOFF,
                note=note or f"Handoff at {now.isoformat()}",
            )

        write_audit(
            action="SAMPLE_COLLECTION_HANDOFF",
            object_type="SampleCollection",
            object_id=collection.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        db.session.commit()
        return collection

    @staticmethod
    def receive_at_lab(
        booking_id,
        note=None,
        actor_email="SYSTEM",
        ip_address="",
        *,
        temperature_c=None,
    ):
        booking = SampleCollectionWorkflowService._get_booking_or_raise(booking_id)
        order = SampleCollectionWorkflowService._get_order_for_booking(booking_id)
        collection = SampleCollection.query.filter_by(
            marketplace_booking_id=booking.id,
        ).filter(
            SampleCollection.status.in_((COLLECTION_COLLECTED, COLLECTION_IN_TRANSIT)),
        ).order_by(SampleCollection.created_at.desc()).first()
        if not collection:
            raise SampleCollectionWorkflowError(
                "Sample must be collected or in transit before lab receive",
                409,
            )

        sample = SampleTracking.query.get(collection.sample_tracking_id)
        if not sample:
            raise SampleCollectionWorkflowError("Sample tracking record not found", 404)

        now = datetime.utcnow()
        sample.status = SAMPLE_RECEIVED
        sample.updated_at = now
        collection.status = COLLECTION_RECEIVED
        collection.arrived_at_lab = now
        collection.updated_at = now
        if temperature_c is not None:
            collection.temperature_c = float(temperature_c)
        order.status = ORDER_LAB_RECEIVED
        booking.updated_at = now

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

        write_audit(
            action="SAMPLE_COLLECTION_LAB_RECEIVED",
            object_type="SampleCollection",
            object_id=collection.id,
            user_email=actor_email,
            ip_address=ip_address,
        )

        db.session.commit()
        return collection, sample

    @staticmethod
    def record_collection_by_id(
        collection_id,
        collector_id=None,
        note=None,
        latitude=None,
        longitude=None,
        actor_email="SYSTEM",
        ip_address="",
        *,
        specimen_type=None,
        scanned_barcode=None,
        collection_location=None,
        require_barcode=False,
        patient_verified=None,
        order_verified=None,
        allow_notes=True,
    ):
        """Collect by SampleCollection id — supports desk (no marketplace booking)."""
        collection = SampleCollectionWorkflowService._get_collection_or_raise(collection_id)
        if collection.marketplace_booking_id:
            return SampleCollectionWorkflowService.record_collection(
                collection.marketplace_booking_id,
                collector_id=collector_id,
                note=note,
                latitude=latitude,
                longitude=longitude,
                actor_email=actor_email,
                ip_address=ip_address,
                specimen_type=specimen_type,
                scanned_barcode=scanned_barcode,
                collection_location=collection_location,
                require_barcode=require_barcode,
                patient_verified=patient_verified,
                order_verified=order_verified,
                allow_notes=allow_notes,
            )

        from app.models.biz_order import BizOrder
        from app.sample_collection_workspace.desk_bridge import (
            ensure_desk_tracking,
            enqueue_sample_and_lab_after_transition,
            sync_biz_collection_from_sample,
        )

        biz_order = BizOrder.query.get(collection.order_id)
        if not biz_order:
            raise SampleCollectionWorkflowError("Desk order not found for collection", 404)

        if collection.status not in (
            COLLECTION_PENDING,
            COLLECTION_CHECKED_IN,
            COLLECTION_RECOLLECT_REQUIRED,
        ):
            raise SampleCollectionWorkflowError(
                f"Sample cannot be collected from status {collection.status}",
                409,
            )

        expected = (
            collection.expected_barcode
            or biz_order.barcode_value
            or f"BC-{biz_order.order_code}"
        )
        collection.expected_barcode = expected

        if require_barcode and not scanned_barcode:
            raise SampleCollectionWorkflowError("scanned_barcode is required", 400)

        if scanned_barcode:
            scanned = SampleCollectionWorkflowService._normalize_barcode(scanned_barcode)
            accepted = {
                SampleCollectionWorkflowService._normalize_barcode(expected),
                SampleCollectionWorkflowService._normalize_barcode(biz_order.order_code),
                SampleCollectionWorkflowService._normalize_barcode(f"BC-{biz_order.order_code}"),
                SampleCollectionWorkflowService._normalize_barcode(biz_order.barcode_value),
            }
            if scanned not in accepted:
                collection.quality_status = SAMPLE_QUALITY_MISMATCHED_ID
                write_audit(
                    action="SAMPLE_COLLECTION_BARCODE_MISMATCH",
                    object_type="SampleCollection",
                    object_id=collection.id,
                    user_email=actor_email,
                    ip_address=ip_address,
                )
                db.session.commit()
                raise SampleCollectionWorkflowError(
                    "Barcode mismatch: scanned identifier does not match expected specimen/order barcode",
                    409,
                )
            collection.barcode_value = scanned_barcode.strip()

        if collector_id:
            collection.collector_id = collector_id
            collector = Driver.query.get(collector_id)
            if collector:
                collection.collector_name = collector.full_name

        now = datetime.utcnow()
        sample = ensure_desk_tracking(collection)
        sample.collector_id = collection.collector_id or sample.collector_id
        sample.latitude = latitude or sample.latitude
        sample.longitude = longitude or sample.longitude
        sample.status = SAMPLE_IN_TRANSIT
        sample.updated_at = now

        collection.status = COLLECTION_COLLECTED
        collection.collected_at = now
        collection.picked_up_at = collection.picked_up_at or now
        collection.specimen_type = specimen_type or collection.specimen_type or "BLOOD"
        collection.collection_location = (
            collection_location or collection.collection_location or "Reception Desk"
        )
        collection.quality_status = SAMPLE_QUALITY_ACCEPTABLE
        collection.updated_at = now
        if patient_verified is not None:
            collection.patient_verified = bool(patient_verified)
        if order_verified is not None:
            collection.order_verified = bool(order_verified)
        if allow_notes and note:
            notes = collection.notes or ""
            if "source:desk" not in notes:
                notes = (notes + "\nsource:desk").strip()
            collection.notes = (notes + f"\n{note}").strip() if note else notes

        SampleCollectionWorkflowService._write_sample_event(
            sample.id,
            SAMPLE_EVENT_COLLECTED,
            note=note or f"Desk sample collected for {biz_order.order_code}",
        )
        write_audit(
            action="SAMPLE_COLLECTION_COLLECTED",
            object_type="SampleCollection",
            object_id=collection.id,
            user_email=actor_email,
            ip_address=ip_address,
        )

        sync_biz_collection_from_sample(collection, actor=actor_email)
        enqueue_sample_and_lab_after_transition(collection, actor=actor_email)
        db.session.commit()
        return collection, sample

    @staticmethod
    def dispatch_by_collection_id(
        collection_id,
        transport_box_id=None,
        note=None,
        actor_email="SYSTEM",
        ip_address="",
        *,
        vehicle_id=None,
        driver_id=None,
        distance_km=None,
        eta_minutes=None,
        temperature_c=None,
        iot_device_id=None,
    ):
        collection = SampleCollectionWorkflowService._get_collection_or_raise(collection_id)
        if collection.marketplace_booking_id:
            return SampleCollectionWorkflowService.dispatch_sample(
                collection.marketplace_booking_id,
                transport_box_id=transport_box_id,
                note=note,
                actor_email=actor_email,
                ip_address=ip_address,
                vehicle_id=vehicle_id,
                driver_id=driver_id,
                distance_km=distance_km,
                eta_minutes=eta_minutes,
                temperature_c=temperature_c,
                iot_device_id=iot_device_id,
            )

        from app.sample_collection_workspace.desk_bridge import (
            ensure_desk_tracking,
            enqueue_sample_and_lab_after_transition,
            sync_biz_collection_from_sample,
        )

        if collection.status != COLLECTION_COLLECTED:
            raise SampleCollectionWorkflowError(
                "Sample must be collected before dispatch",
                409,
            )

        sample = ensure_desk_tracking(collection)
        now = datetime.utcnow()
        if transport_box_id:
            sample.transport_box_id = transport_box_id
            collection.transport_box_id = transport_box_id
        sample.status = SAMPLE_IN_TRANSIT
        sample.updated_at = now
        collection.status = COLLECTION_IN_TRANSIT
        collection.dispatched_at = now
        collection.updated_at = now
        if vehicle_id:
            collection.vehicle_id = vehicle_id
        if driver_id:
            collection.driver_id = driver_id
        if distance_km is not None:
            collection.distance_km = float(distance_km)
        if eta_minutes is not None:
            collection.eta_minutes = int(eta_minutes)
        if temperature_c is not None:
            collection.temperature_c = float(temperature_c)
        if iot_device_id:
            collection.iot_device_id = iot_device_id

        SampleCollectionWorkflowService._write_sample_event(
            sample.id,
            SAMPLE_EVENT_DISPATCH,
            note=note or f"Desk dispatch at {now.isoformat()}",
        )
        write_audit(
            action="SAMPLE_COLLECTION_DISPATCHED",
            object_type="SampleCollection",
            object_id=collection.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        sync_biz_collection_from_sample(collection, actor=actor_email)
        enqueue_sample_and_lab_after_transition(collection, actor=actor_email)
        db.session.commit()
        return collection, sample

    @staticmethod
    def receive_by_collection_id(
        collection_id,
        note=None,
        actor_email="SYSTEM",
        ip_address="",
        *,
        temperature_c=None,
    ):
        collection = SampleCollectionWorkflowService._get_collection_or_raise(collection_id)
        if collection.marketplace_booking_id:
            return SampleCollectionWorkflowService.receive_at_lab(
                collection.marketplace_booking_id,
                note=note,
                actor_email=actor_email,
                ip_address=ip_address,
                temperature_c=temperature_c,
            )

        from app.sample_collection_workspace.desk_bridge import (
            ensure_desk_tracking,
            enqueue_sample_and_lab_after_transition,
            sync_biz_collection_from_sample,
        )

        if collection.status not in (COLLECTION_COLLECTED, COLLECTION_IN_TRANSIT):
            raise SampleCollectionWorkflowError(
                "Sample must be collected or in transit before lab receive",
                409,
            )

        sample = ensure_desk_tracking(collection)
        now = datetime.utcnow()
        sample.status = SAMPLE_RECEIVED
        sample.updated_at = now
        collection.status = COLLECTION_RECEIVED
        collection.arrived_at_lab = now
        collection.updated_at = now
        if temperature_c is not None:
            collection.temperature_c = float(temperature_c)

        SampleCollectionWorkflowService._write_sample_event(
            sample.id,
            SAMPLE_EVENT_LAB_RECEIVED,
            note=note or f"Desk sample received at lab at {now.isoformat()}",
        )
        write_audit(
            action="SAMPLE_COLLECTION_LAB_RECEIVED",
            object_type="SampleCollection",
            object_id=collection.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        sync_biz_collection_from_sample(collection, actor=actor_email)
        enqueue_sample_and_lab_after_transition(collection, actor=actor_email)
        db.session.commit()
        return collection, sample

    @staticmethod
    def get_audit_trail(collection_id):
        collection = SampleCollectionWorkflowService._get_collection_or_raise(collection_id)
        audits = (
            AuditLog.query.filter_by(
                object_type="SampleCollection",
                object_id=collection.id,
            )
            .order_by(AuditLog.created_at.asc())
            .all()
        )
        events = []
        if collection.sample_tracking_id:
            events = (
                SampleEvent.query.filter_by(sample_tracking_id=collection.sample_tracking_id)
                .order_by(SampleEvent.created_at.asc())
                .all()
            )
        return {
            "collection_id": collection.id,
            "audits": [a.to_dict() for a in audits],
            "sample_events": [e.to_dict() for e in events],
        }

    @staticmethod
    def transport_status(collection_id):
        collection = SampleCollectionWorkflowService._get_collection_or_raise(collection_id)
        return {
            "collection_id": collection.id,
            "status": collection.status,
            "picked_up_at": collection.picked_up_at.isoformat() if collection.picked_up_at else None,
            "dispatched_at": collection.dispatched_at.isoformat() if collection.dispatched_at else None,
            "handoff_at": collection.handoff_at.isoformat() if collection.handoff_at else None,
            "arrived_at_lab": collection.arrived_at_lab.isoformat() if collection.arrived_at_lab else None,
            "vehicle_id": collection.vehicle_id,
            "driver_id": collection.driver_id,
            "transport_box_id": collection.transport_box_id,
            "distance_km": collection.distance_km,
            "eta_minutes": collection.eta_minutes,
            "temperature_c": collection.temperature_c,
            "iot_device_id": collection.iot_device_id,
        }
